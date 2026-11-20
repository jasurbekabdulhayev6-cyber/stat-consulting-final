import os, glob, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("outputs", exist_ok=True)
defects = []

def log_defect(q, col_type, detail):
    defects.append({"savol": q, "tur": col_type, "tavsif": detail})

def pick_col(cols, candidates):
    low_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in low_map:
            return low_map[cand.lower()]
    for cand in candidates:
        for c in cols:
            if cand.lower() in c.lower():
                return c
    return None

def ci95(arr):
    s = pd.Series(arr).dropna().astype(float)
    n = len(s)
    if n < 2:
        return (np.nan, np.nan, n)
    m = s.mean()
    se = s.std(ddof=1) / np.sqrt(n)
    return (m - 1.96 * se, m + 1.96 * se, n)

panel_path = "data/panel_q1_q9.csv"
if not os.path.exists(panel_path):
    csvs = glob.glob("data/*.csv")
    if not csvs:
        csvs = glob.glob("**/*.csv", recursive=True)
    panel_path = csvs[0]

df = pd.read_csv(panel_path, low_memory=False)
cols = list(df.columns)

date_col = pick_col(cols, ["date", "dt", "trade_date", "bas_dt", "ym"])
ticker_col = pick_col(cols, ["ticker", "symbol", "code", "stock_code", "company", "name"])
sector_col = pick_col(cols, ["sector", "gics_sector", "industry", "wics_sector", "업종", "섹터"])
ret_col = pick_col(cols, ["return", "ret", "daily_return", "pct_change", "r"])
opm_col = pick_col(cols, ["operating_margin", "opm", "op_margin", "operating_profit_margin"])
op_inc_col = pick_col(cols, ["operating_income", "ebit", "op_profit", "영업이익"])
rev_col = pick_col(cols, ["revenue", "sales", "turnover", "매출액"])
earn_date_col = pick_col(cols, ["earnings_date", "ann_date", "report_date", "disclosure_date", "earnings_change"])
actual_eps_col = pick_col(cols, ["actual_eps", "actual", "eps_actual", "reported_eps"])
est_eps_col = pick_col(cols, ["est_eps", "estimate", "consensus_eps", "eps_est", "forecast"])
debt_col = pick_col(cols, ["debt_ratio", "debt_to_equity", "leverage", "liabilities_ratio", "debt"])
pbr_col = pick_col(cols, ["pbr", "pb", "price_to_book", "p_b"])
roe_col = pick_col(cols, ["roe", "return_on_equity"])

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.sort_values([c for c in [ticker_col, date_col] if c]).reset_index(drop=True)

if ret_col is None:
    price_col = pick_col(cols, ["close", "adj_close", "price"])
    if price_col and ticker_col:
        df["_ret"] = df.groupby(ticker_col)[price_col].pct_change()
        ret_col = "_ret"
        log_defect("Q5-Q9", "proxy_return", f"{price_col} dan pct_change hisoblandi")
    else:
        raise RuntimeError(f"Return ustuni topilmadi. Mavjud ustunlar: {cols}")

df[ret_col] = pd.to_numeric(df[ret_col], errors="coerce")
if sector_col is None:
    df["_sector"] = "All_Market"
    sector_col = "_sector"
    log_defect("Q5-Q9", "missing_sector", "Sektor ustuni topilmadi; All_Market ishlatildi")
else:
    df[sector_col] = df[sector_col].fillna("Unknown").astype(str)

report_lines = ["=== SAVOLLAR 5-9 YAKUNIY HISOBOTI ===", f"Fayl: {panel_path} | Qatorlar: {len(df)}"]
results = {"file": panel_path, "rows": int(len(df)), "columns": cols}

# Savol 5: Operatsion marja vs Jamlanma daromad
if opm_col is None and op_inc_col and rev_col:
    df["_opm"] = pd.to_numeric(df[op_inc_col], errors="coerce") / pd.to_numeric(df[rev_col], errors="coerce").replace(0, np.nan)
    opm_col = "_opm"
    log_defect("Q5", "proxy_opm", f"{op_inc_col}/{rev_col} dan operatsion marja hisoblandi")

if opm_col:
    df[opm_col] = pd.to_numeric(df[opm_col], errors="coerce")
    sec5 = df.groupby(sector_col).agg(
        mean_opm=(opm_col, "mean"),
        first_opm=(opm_col, lambda s: s.dropna().iloc[0] if len(s.dropna()) else np.nan),
        last_opm=(opm_col, lambda s: s.dropna().iloc[-1] if len(s.dropna()) else np.nan),
        cum_ret=(ret_col, lambda s: (1.0 + s.dropna()).prod() - 1.0 if len(s.dropna()) else np.nan),
        n_obs=(ret_col, "count")
    ).dropna(subset=["mean_opm", "cum_ret"])
    sec5["opm_change"] = sec5["last_opm"] - sec5["first_opm"]
    sec5["margin_regime"] = np.where(
        sec5["opm_change"] > sec5["opm_change"].median(),
        "Margin_Rising_Above_Med",
        np.where(sec5["first_opm"] > sec5["first_opm"].median(), "High_From_Start", "Other")
    )
    corr5 = sec5["mean_opm"].corr(sec5["cum_ret"])
    within_corr = np.nan
    if ticker_col:
        comp5 = df.groupby([sector_col, ticker_col]).agg(
            c_opm=(opm_col, "mean"),
            c_cum_ret=(ret_col, lambda s: (1.0 + s.dropna()).prod() - 1.0 if len(s.dropna()) else np.nan)
        ).dropna()
        if len(comp5) > 2:
            within_corr = comp5.groupby(sector_col).apply(lambda g: g["c_opm"].corr(g["c_cum_ret"]) if len(g) > 2 else np.nan).mean()
    lo5, hi5, n5 = ci95(sec5["cum_ret"])
    results["Q5"] = {
        "sector_corr_opm_cumret": float(corr5) if pd.notna(corr5) else None,
        "within_sector_mean_corr": float(within_corr) if pd.notna(within_corr) else None,
        "cum_ret_ci95": [float(lo5) if pd.notna(lo5) else None, float(hi5) if pd.notna(hi5) else None, int(n5)],
        "regime_mean_cum_ret": sec5.groupby("margin_regime")["cum_ret"].mean().to_dict()
    }
    report_lines.append(f"\n--- Q5: Sektor korr={corr5:.4f}, Sektor-ichki o'rtacha korr={within_corr:.4f} ---")
    report_lines.append(sec5.sort_values("cum_ret", ascending=False).head(15).to_string())

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sec5["mean_opm"], sec5["cum_ret"])
    for idx, r in sec5.iterrows():
        ax.annotate(str(idx)[:12], (r["mean_opm"], r["cum_ret"]), fontsize=8)
    ax.set_title("Q5: Operatsion marja vs Jamlanma daromad (sektorlar)")
    ax.set_xlabel("O'rtacha operatsion marja")
    ax.set_ylabel("Jamlanma daromad")
    plt.tight_layout()
    plt.savefig("outputs/grafik_5_marja_daromad.png", dpi=150)
    plt.close()
else:
    log_defect("Q5", "missing_col", "Operatsion marja ustuni topilmadi")
    results["Q5"] = {"status": "missing_operating_margin"}

# Savol 6: Hisobot e'loni atrofida [-10, +10] reaksiya
event_mask = pd.Series(False, index=df.index)
if earn_date_col and earn_date_col in df.columns:
    s_ed = df[earn_date_col].astype(str)
    if date_col and ticker_col:
        prev_ed = df.groupby(ticker_col)[earn_date_col].shift(1).astype(str)
        event_mask = (s_ed != prev_ed) & df[earn_date_col].notna()
    else:
        event_mask = df[earn_date_col].notna() & (df[earn_date_col].ne(0))

win_stats = {}
if event_mask.sum() > 0 and ticker_col and date_col:
    df["_pos"] = df.groupby(ticker_col).cumcount()
    ev_rows = df[event_mask][[ticker_col, "_pos"]].drop_duplicates()
    for k in range(-10, 11):
        sub = ev_rows.copy()
        sub["_target_pos"] = sub["_pos"] + k
        merged = sub.merge(df[[ticker_col, "_pos", ret_col]], left_on=[ticker_col, "_target_pos"], right_on=[ticker_col, "_pos"], how="inner")
        lo, hi, n = ci95(merged[ret_col])
        win_stats[str(k)] = {
            "mean_ret": float(merged[ret_col].mean()) if n else None,
            "ci95": [float(lo) if pd.notna(lo) else None, float(hi) if pd.notna(hi) else None],
            "n": int(n)
        }
    results["Q6"] = {"n_events": int(len(ev_rows)), "event_window_daily_ret": win_stats}
    report_lines.append(f"\n--- Q6: Hodisalar soni={len(ev_rows)} ---")
    for k in [-10, -5, -1, 0, 1, 2, 3, 5, 10]:
        st = win_stats.get(str(k), {})
        report_lines.append(f"  t={k:+d}: mean={st.get('mean_ret')}, n={st.get('n')}")

    ks = list(range(-10, 11))
    means = [win_stats[str(k)]["mean_ret"] or 0.0 for k in ks]
    cum_means = np.cumsum(means)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, cum_means, marker="o")
    ax.axvline(0, linestyle="--")
    ax.set_title("Q6: Hisobot e'loni atrofida [-10, +10] jamlanma daromad")
    ax.set_xlabel("E'longa nisbatan kunlar (t)")
    ax.set_ylabel("Jamlanma o'rtacha daromad")
    plt.tight_layout()
    plt.savefig("outputs/grafik_6_hisobot_reaksiya.png", dpi=150)
    plt.close()
else:
    log_defect("Q6", "missing_earnings_events", "Earnings o'zgarish kunlari yoki panel tuzilmasi topilmadi")
    results["Q6"] = {"status": "insufficient_earnings_event_data"}

# Savol 7: Prognoz xatosi va qayta ko'rib chiqishlar
err_col = pick_col(cols, ["est_error", "forecast_error", "eps_error", "error"])
if err_col is None and actual_eps_col and est_eps_col:
    df["_est_err"] = pd.to_numeric(df[actual_eps_col], errors="coerce") - pd.to_numeric(df[est_eps_col], errors="coerce")
    err_col = "_est_err"
    log_defect("Q7", "proxy_est_err", f"{actual_eps_col} - {est_eps_col} dan prognoz xatosi hisoblandi")

if err_col:
    df[err_col] = pd.to_numeric(df[err_col], errors="coerce")
    sec7 = df.groupby(sector_col)[err_col].agg(
        count="count",
        mean="mean",
        std="std",
        abs_mean=lambda s: s.abs().mean(),
        positive_share=lambda s: (s > 0).mean()
    ).dropna()
    rev_info = {}
    if est_eps_col and ticker_col:
        df["_rev"] = pd.to_numeric(df[est_eps_col], errors="coerce").groupby(df[ticker_col]).diff()
        rev_info = df.groupby(sector_col)["_rev"].agg(["count", "mean", "std"]).dropna().to_dict(orient="index")
    results["Q7"] = {"by_sector": sec7.to_dict(orient="index"), "revisions_by_sector": rev_info}
    report_lines.append("\n--- Q7: Prognoz xatosi (sektorlar kesimida) ---")
    report_lines.append(sec7
