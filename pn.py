import csv
import glob
import json
import os
import re
from multiprocessing import Pool, cpu_count

OUT_DIR = "data/daily_q1_q9"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

FOLDERS = sorted(glob.glob("/mnt/data/stock/20*"))
TOTAL_FOLDERS = len(FOLDERS)
DEFECT_FILE = "logs/defect_log_q1_q9.csv"
PROOF_FILE = "logs/coverage_proof_q1_q9.csv"

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
CODE_RE = re.compile(r"_(\d{6})\.html$")
NAME_RE = re.compile(r'class="wrap_company"[^>]*>.*?<h2[^>]*>.*?<a[^>]*>([^<]+)</a>', re.S)
SEC_RE = re.compile(r'href="[^"]*sise_group_detail[^"]*"[^>]*>([^<]+)</a>', re.S)
CLOSE_RE = re.compile(r'class="no_today"[^>]*>.*?<span class="blind">([^<]+)</span>', re.S)
TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
TH_TD_RE = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.S | re.I)

FIN_KEYWORDS = (
    "매출액", "영업이익", "당기순이익", "자산총계", "부채총계", "자본총계",
    "영업이익률", "순이익률", "ROE", "ROA", "부채비율", "당좌비율",
    "유보율", "PER", "PBR", "EPS", "BPS", "배당수익률", "주당배당금"
)


def clean_text(html_frag: str) -> str:
    txt = TAG_RE.sub(" ", html_frag)
    txt = (
        txt.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return WS_RE.sub(" ", txt).strip()


def clean_num(val: str) -> str:
    return re.sub(r"[^\d.-]", "", val)


def parse_single_file(fpath: str):
    fname = os.path.basename(fpath)
    m_code = CODE_RE.search(fname)
    code = m_code.group(1) if m_code else fname.replace(".html", "")
    defects = []

    try:
        with open(fpath, "rb") as f:
            raw = f.read()

        if len(raw) < 500:
            defects.append((fname, code, "EMPTY_OR_TINY_FILE", f"size={len(raw)}"))
            return None, defects

        txt = None
        for enc in ("cp949", "euc-kr", "utf-8"):
            try:
                txt = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if txt is None:
            txt = raw.decode("cp949", errors="replace")
            defects.append((fname, code, "ENCODING_REPLACE", "cp949 fallback"))

        m_name = NAME_RE.search(txt)
        name = clean_text(m_name.group(1)) if m_name else ""

        m_sec = SEC_RE.search(txt)
        sector = clean_text(m_sec.group(1)) if m_sec else ""

        m_close = CLOSE_RE.search(txt)
        close_val = clean_num(m_close.group(1)) if m_close else ""

        market = ""
        for mkt in ("KOSPI", "KOSDAQ", "KONEX"):
            if re.search(rf"\b{mkt}\b", txt):
                market = mkt
                break

        kv = {}
        fin_rows = []
        for tr_m in TR_RE.finditer(txt):
            cells = [clean_text(c) for c in TH_TD_RE.findall(tr_m.group(1))]
            cells = [c for c in cells if c]
            if len(cells) >= 2:
                key = cells[0]
                if key not in kv:
                    kv[key] = cells[1]
                if any(k in key for k in FIN_KEYWORDS):
                    fin_rows.append(cells)

        open_val = clean_num(kv.get("시가", ""))
        high_val = clean_num(kv.get("고가", ""))
        low_val = clean_num(kv.get("저가", ""))
        vol_val = clean_num(kv.get("거래량", ""))
        tval_val = clean_num(kv.get("거래대금", ""))
        mktcap_val = clean_num(kv.get("시가총액", ""))
        shares_val = clean_num(kv.get("상장주식수", ""))
        per_val = clean_num(kv.get("PER", "") or kv.get("추정PER", ""))
        pbr_val = clean_num(kv.get("PBR", ""))
        eps_val = clean_num(kv.get("EPS", ""))
        bps_val = clean_num(kv.get("BPS", ""))
        div_val = clean_num(kv.get("배당수익률", ""))
        for_val = clean_num(kv.get("외국인소진율", ""))

        if not close_val:
            defects.append((fname, code, "MISSING_CLOSE", name))
        if not sector:
            defects.append((fname, code, "MISSING_SECTOR", name))
        if not mktcap_val:
            defects.append((fname, code, "MISSING_MKTCAP", name))

        fin_json = json.dumps(fin_rows, ensure_ascii=False) if fin_rows else ""

        row = [
            code, name, market, sector,
            close_val, open_val, high_val, low_val,
            vol_val, tval_val, mktcap_val, shares_val,
            per_val, pbr_val, eps_val, bps_val, div_val, for_val,
            fin_json,
        ]
        return row, defects

    except Exception as e:
        defects.append((fname, code, "PARSE_EXCEPTION", str(e)[:120]))
        return None, defects


def process_folder(args):
    idx, folder = args
    date_str = os.path.basename(folder)
    out_csv = os.path.join(OUT_DIR, f"{date_str}.csv")

    if os.path.exists(out_csv):
        return f"[{idx}/{TOTAL_FOLDERS}] {date_str}: already processed (skipped).", []

    html_files = sorted(glob.glob(folder + "/*.html"))
    rows_out = []
    day_defects = []

    for fpath in html_files:
        row, defects = parse_single_file(fpath)
        if row is not None:
            rows_out.append([date_str] + row)
        for fname, code, dtype, detail in defects:
            day_defects.append([date_str, fname, code, dtype, detail])

    with open(out_csv, "w", newline="", encoding="utf-8") as f_csv:
        w = csv.writer(f_csv)
        w.writerow([
            "date", "code", "name", "market", "sector",
            "close", "open", "high", "low",
            "volume", "trading_value", "mktcap", "shares",
            "per", "pbr", "eps", "bps", "dividend_yield", "foreign_ownership",
            "financials_json",
        ])
        w.writerows(rows_out)

    msg = f"[{idx}/{TOTAL_FOLDERS}] {date_str}: saved {len(rows_out)}/{len(html_files)} stocks."
    return msg, day_defects


def write_proof_table(defect_file, proof_file):
    defect_counts = {}
    if os.path.exists(defect_file):
        with open(defect_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d = row.get("date", "")
                defect_counts[d] = defect_counts.get(d, 0) + 1

    total_html_all = 0
    total_saved_all = 0
    missing_days = 0

    with open(proof_file, "w", newline="", encoding="utf-8") as pf:
        writer = csv.writer(pf)
        writer.writerow([
            "date", "archive_html_files", "saved_csv_rows",
            "defect_log_entries", "status",
        ])

        for folder in FOLDERS:
            date_str = os.path.basename(folder)
            html_count = len(glob.glob(folder + "/*.html"))
            csv_path = os.path.join(OUT_DIR, f"{date_str}.csv")
            total_html_all += html_count
            d_cnt = defect_counts.get(date_str, 0)

            if not os.path.exists(csv_path):
                missing_days += 1
                writer.writerow([date_str, html_count, 0, d_cnt, "MISSING_CSV"])
                continue

            with open(csv_path, "r", encoding="utf-8") as cf:
                saved_rows = max(0, sum(1 for _ in cf) - 1)
            total_saved_all += saved_rows
            status = (
                "VERIFIED_COMPLETE"
                if saved_rows == html_count and d_cnt == 0
                else "VERIFIED_WITH_NOTES"
            )
            writer.writerow([date_str, html_count, saved_rows, d_cnt, status])

    return (
        TOTAL_FOLDERS,
        missing_days,
        total_html_all,
        total_saved_all,
        sum(defect_counts.values()),
    )


if __name__ == "__main__":
    write_header = not os.path.exists(DEFECT_FILE)
    with open(DEFECT_FILE, "a", newline="", encoding="utf-8") as df_out:
        defect_writer = csv.writer(df_out)
        if write_header:
            defect_writer.writerow(["date", "file", "code", "defect_type", "detail"])

        workers = min(8, max(2, cpu_count() or 4))
        tasks = list(enumerate(FOLDERS, start=1))

        with Pool(processes=workers) as pool:
            for done_cnt, (msg, day_defects) in enumerate(
                pool.imap_unordered(process_folder, tasks), start=1
            ):
                if day_defects:
                    defect_writer.writerows(day_defects)
                if done_cnt % 15 == 0 or done_cnt == TOTAL_FOLDERS:
                    print(f"Progress {done_cnt}/{TOTAL_FOLDERS} | {msg}", flush=True)

    total_f, miss_d, tot_html, tot_saved, tot_def = write_proof_table(
        DEFECT_FILE, PROOF_FILE
    )
    print("\n=== ARCHIVE EXTRACTION PROOF SUMMARY (Q1-Q9) ===")
    print(f"Total trading-day folders in archive: {total_f}")
    print(f"Missing daily CSV files: {miss_d}")
    print(f"Total HTML files scanned: {tot_html}")
    print(f"Total stock rows saved to CSV: {tot_saved}")
    print(f"Total defect log entries: {tot_def}")
    print(f"Proof table saved to: {PROOF_FILE}")
    print(f"Defect log saved to: {DEFECT_FILE}")
