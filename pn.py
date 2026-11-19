import csv
import glob
import os
import re
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup

os.makedirs("data/daily", exist_ok=True)
os.makedirs("logs", exist_ok=True)

FOLDERS = sorted(glob.glob("/mnt/data/stock/20*"))
TOTAL_FOLDERS = len(FOLDERS)
DEFECT_FILE = "logs/defect_log_q1_q4.csv"
PROOF_FILE = "logs/coverage_proof.csv"


def parse_single_file(fpath):
    fname = os.path.basename(fpath)
    m_code = re.search(r"_(\d{6})\.html$", fname)
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

        soup = BeautifulSoup(txt, "html.parser")

        name_tag = soup.select_one(".wrap_company h2 a")
        name = name_tag.get_text(strip=True) if name_tag else ""

        sec_tag = soup.select_one('a[href*="sise_group_detail"]')
        sector = sec_tag.get_text(strip=True) if sec_tag else ""

        close_tag = soup.select_one(".no_today .blind")
        close_val = re.sub(r"[^\d.]", "", close_tag.get_text()) if close_tag else ""

        vol_val = ""
        for td in soup.select("table.no_info td"):
            if "거래량" in td.get_text(" ", strip=True):
                b = td.select_one(".blind")
                if b:
                    vol_val = re.sub(r"[^\d]", "", b.get_text())
                    break

        mktcap_val = ""
        for tr in soup.select("table tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            if "시가총액" in th.get_text(" ", strip=True):
                mktcap_val = re.sub(r"[^\d]", "", td.get_text(" ", strip=True))
                break

        if not close_val:
            defects.append((fname, code, "MISSING_CLOSE", name))
        if not sector:
            defects.append((fname, code, "MISSING_SECTOR", name))
        if not mktcap_val:
            defects.append((fname, code, "MISSING_MKTCAP", name))

        return [code, name, sector, close_val, mktcap_val, vol_val], defects

    except Exception as e:
        defects.append((fname, code, "PARSE_EXCEPTION", str(e)[:120]))
        return None, defects


def process_folder(args):
    idx, folder = args
    date_str = os.path.basename(folder)
    out_csv = f"data/daily/{date_str}.csv"

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
        w.writerow(["date", "code", "name", "sector", "close", "mktcap", "volume"])
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
        writer.writerow(["date", "archive_html_files", "saved_csv_rows", "defect_log_entries", "status"])

        for folder in FOLDERS:
            date_str = os.path.basename(folder)
            html_count = len(glob.glob(folder + "/*.html"))
            csv_path = f"data/daily/{date_str}.csv"
            total_html_all += html_count
            d_cnt = defect_counts.get(date_str, 0)

            if not os.path.exists(csv_path):
                missing_days += 1
                writer.writerow([date_str, html_count, 0, d_cnt, "MISSING_CSV"])
                continue

            with open(csv_path, "r", encoding="utf-8") as cf:
                saved_rows = max(0, sum(1 for _ in cf) - 1)
            total_saved_all += saved_rows
            status = "VERIFIED_COMPLETE" if saved_rows == html_count and d_cnt == 0 else "VERIFIED_WITH_NOTES"
            writer.writerow([date_str, html_count, saved_rows, d_cnt, status])

    return TOTAL_FOLDERS, missing_days, total_html_all, total_saved_all, sum(defect_counts.values())


if __name__ == "__main__":
    write_header = not os.path.exists(DEFECT_FILE)
    with open(DEFECT_FILE, "a", newline="", encoding="utf-8") as df_out:
        defect_writer = csv.writer(df_out)
        if write_header:
            defect_writer.writerow(["date", "file", "code", "defect_type", "detail"])

        workers = min(8, max(2, cpu_count() or 4))
        tasks = list(enumerate(FOLDERS, start=1))

        with Pool(processes=workers) as pool:
            for done_cnt, (msg, day_defects) in enumerate(pool.imap_unordered(process_folder, tasks), start=1):
                if day_defects:
                    defect_writer.writerows(day_defects)
                if done_cnt % 15 == 0 or done_cnt == TOTAL_FOLDERS:
                    print(f"Progress {done_cnt}/{TOTAL_FOLDERS} | {msg}", flush=True)

    total_f, miss_d, tot_html, tot_saved, tot_def = write_proof_table(DEFECT_FILE, PROOF_FILE)
    print("\n=== ARCHIVE EXTRACTION PROOF SUMMARY ===")
    print(f"Total trading-day folders in archive: {total_f}")
    print(f"Missing daily CSV files: {miss_d}")
    print(f"Total HTML files scanned: {tot_html}")
    print(f"Total stock rows saved to CSV: {tot_saved}")
    print(f"Total defect log entries: {tot_def}")
    print(f"Proof table saved to: {PROOF_FILE}")
    print(f"Defect log saved to: {DEFECT_FILE}")
