import os
import glob
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("outputs", exist_ok=True)
defects = []


def log_defect(q, issue_type, detail):
    defects.append({"question": q, "type": issue_type, "detail": detail})


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


def find_panel_csv():
    for path in ["data/panel_q1_q9.csv", "panel_q1_q9.csv"]:
        if os.path.exists(path):
            return path

    all_csvs = sorted(
        set(
            glob.glob("**/*.csv", recursive=True)
            + glob.glob("/home/s202555471/**/*.csv", recursive=True)
            + glob.glob("/mnt/data/**/*.csv", recursive=True)
        )
    )
    for p in all_csvs:
        bn = os.path.basename(p).lower()
        if "panel" in bn or "q1_q9" in bn:
            return p

    best_path = None
    best_cols = -1
    for p in all_csvs:
        bn = os.path.basename(p).lower()
        if "defect" in bn or "issue" in bn:
            continue
        try:
            tmp = pd.read_csv(p, nrows=5)
            if len(tmp.columns) > best_cols:
                best_cols = len(tmp.columns)
                best_path = p
        except Exception:
            continue

    if best_path:
        return best_path
    raise FileNotFoundError("No panel CSV found. Run pn.py or provide panel_q1_q9.csv.")


panel_path = find_panel_csv()
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
        log_defect("Q5-Q9", "proxy_return", f"Computed return via pct_change from {price_col}")
    elif price_col:
        df["_ret"] = pd.to_numeric(df[price_col], errors="coerce").pct_change()
        ret_col = "_ret"
        log_defect("Q5-Q9", "proxy_return_no_ticker", f"Computed return via pct_change from {price_col}")
    else:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            ret_col = num_cols[0]
            log_defect("Q5-Q9", "fallback_numeric", f"No return column found; used {ret_col}")
        else:
            raise RuntimeError(f"No return or numeric column found. Available columns: {cols}")

df[ret_col] = pd.to_numeric(df[ret_col], errors="coerce")

if sector_col is None:
    df["_sector"] = "All_Market"
    sector_col = "_sector"
    log_defect("Q5-Q9", "missing_sector", "Sector column missing; used All_Market")
else:
    df[sector_col] = df[sector_col].fillna("Unknown").astype(str)

report_lines = [
    "=== QUESTIONS 5-9 FINAL REPORT ===",
    f"File: {panel_path} | Rows: {len(df)} | Columns: {cols}",
]
results = {"file": panel_path, "rows": int(len(df)), "columns": cols}

# Q5: Operating margin vs cumulative return
if opm_col is None and op_inc_col and rev_col:
    denom = pd.to_numeric(df[rev_col], errors="coerce").replace(0, np.nan)
    df["_opm"] = pd.to_numeric(df[op_inc_col], errors="coerce") / denom
    opm_col = "_opm"
    log_defect("Q5", "proxy_opm", f"Computed operating margin from {op_inc_col}/{rev_col}")

if opm_col:
    df[opm_col] = pd.to_numeric(df[opm_col], errors="coerce")
    sec5 = df.groupby(sector_col).agg(
        mean_opm=(opm_col, "mean"),
        first_opm=(opm_col, lambda s: s.dropna().iloc[0] if len(s.dropna()) else np.nan),
        last_opm=(opm_col, lambda s: s.dropna().iloc[-1] if len(s.dropna()) else np.nan),
        cum_ret=(ret_col, lambda s: (1.0 + s.dropna()).prod() - 1.0 if len(s.dropna()) else np.nan),
        n_obs=(ret_col, "count"),
    ).dropna(subset=["mean_opm", "cum_ret"])

    sec5["opm_change"] = sec5["last_opm"] - sec5["first_opm"]
    sec5["margin_regime"] = np.where(
        sec5["opm_change"] > sec5["opm_change"].median(),
        "Margin_Rising_Above_Med",
        np.where(sec5["first_opm"] > sec5["first_opm"].median(), "High_From_Start", "Other"),
    )
    corr5 = sec5["mean_opm"].corr(sec5["cum_ret"])
    within_corr = np.nan
    if ticker_col:
        comp5 = df.groupby([sector_col, ticker_col]).agg(
            c_opm=(opm_col, "mean"),
            c_cum_ret=(ret_col, lambda s: (1.0 + s.dropna()).prod() - 1.0 if len(s.dropna()) else np.nan),
        ).dropna()
        if len(comp5) > 2:
            within_corr = comp5.groupby(sector_col).apply(
                lambda g: g["c_opm"].corr(g["c_cum_ret"]) if len(g) > 2 else np.nan,
                include_groups=False,
            ).mean()

    lo5, hi5, n5 = ci95(sec5["cum_ret"])
    results["Q5"] = {
        "sector_corr_opm_cumret": float(corr5) if pd.notna(corr5) else None,
        "within_sector_mean_corr": float(within_corr) if pd.notna(within_corr) else None,
        "cum_ret_ci95": [float(lo5) if pd.notna(lo5) else None, float(hi5) if pd.notna(hi5) else None, int(n5)],
        "regime_mean_cum_ret": sec5.groupby("margin_regime")["cum_ret"].mean().to_dict(),
    }
    report_lines.append(f"\n--- Q5: Sector corr={corr5}, Within-sector mean corr={within_corr} ---")
    report_lines.append(sec5.sort_values("cum_ret", ascending=False).head(15).to_string())

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sec5["mean_opm"], sec5["cum_ret"])
    for idx, r in sec5.iterrows():
        ax.annotate(str(idx)[:12], (r["mean_opm"], r["cum_ret"]), fontsize=8)
    ax.set_title("Q5: Operating Margin vs Cumulative Return (By Sector)")
    ax.set_xlabel("Mean Operating Margin")
    ax.set_ylabel("Cumulative Return")
    plt.tight_layout()
    plt.savefig("outputs/chart_5_margin_return.png", dpi=150)
    plt.close()
else:
    log_defect("Q5", "missing_col", "Operating margin column not found")
    results["Q5"] = {"status": "missing_operating_margin"}

# Q6: Event window [-10, +10] around earnings announcements
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
        merged = sub.merge(
            df[[ticker_col, "_pos", ret_col]],
            left_on=[ticker_col, "_target_pos"],
            right_on=[ticker_col, "_pos"],
            how="inner",
        )
        lo, hi, n = ci95(merged[ret_col])
        win_stats[str(k)] = {
            "mean_ret": float(merged[ret_col].mean()) if n else None,
            "ci95": [float(lo) if pd.notna(lo) else None, float(hi) if pd.notna(hi) else None],
            "n": int(n),
        }
    results["Q6"] = {"n_events": int(len(ev_rows)), "event_window_daily_ret": win_stats}
    report_lines.append(f"\n--- Q6: Events count={len(ev_rows)} ---")
    for k in [-10, -5, -1, 0, 1, 2, 3, 5, 10]:
        st = win_stats.get(str(k), {})
        report_lines.append(f"  t={k:+d}: mean={st.get('mean_ret')}, ci95={st.get('ci95')}, n={st.get('n')}")

    ks = list(range(-10, 11))
    means = [win_stats[str(k)]["mean_ret"] or 0.0 for k in ks]
    cum_means = np.cumsum(means)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, cum_means, marker="o")
    ax.axvline(0, linestyle="--")
    ax.set_title("Q6: Cumulative Return [-10, +10] Around Earnings")
    ax.set_xlabel("Days Relative to Event (t)")
    ax.set_ylabel("Cumulative Mean Return")
    plt.tight_layout()
    plt.savefig("outputs/chart_6_earnings_reaction.png", dpi=150)
    plt.close()
else:
    log_defect("Q6", "missing_earnings_events", "Earnings event dates or panel structure not found")
    results["Q6"] = {"status": "insufficient_earnings_event_data"}

# Q7: Forecast error and revisions
err_col = pick_col(cols, ["est_error", "forecast_error", "eps_error", "error"])
if err_col is None and actual_eps_col and est_eps_col:
    df["_est_err"] = pd.to_numeric(df[actual_eps_col], errors="coerce") - pd.to_numeric(df[est_eps_col], errors="coerce")
    err_col = "_est_err"
    log_defect("Q7", "proxy_est_err", f"Computed forecast error from {actual_eps_col} - {est_eps_col}")

if err_col:
    df[err_col] = pd.to_numeric(df[err_col], errors="coerce")
    sec7 = df.groupby(sector_col)[err_col].agg(
        count="count",
        mean="mean",
        std="std",
        abs_mean=lambda s: s.abs().mean(),
        positive_share=lambda s: (s > 0).mean(),
    ).dropna()
    rev_info = {}
    if est_eps_col and ticker_col:
        df["_rev"] = pd.to_numeric(df[est_eps_col], errors="coerce").groupby(df[ticker_col]).diff()
        rev_info = df.groupby(sector_col)["_rev"].agg(["count", "mean", "std"]).dropna().to_dict(orient="index")
    results["Q7"] = {"by_sector": sec7.to_dict(orient="index"), "revisions_by_sector": rev_info}
    report_lines.append("\n--- Q7: Forecast Error by Sector ---")
    report_lines.append(sec7.sort_values("abs_mean", ascending=False).head(15).to_string())

    top7 = sec7.sort_values("abs_mean", ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top7.index.astype(str)[::-1], top7["abs_mean"].iloc[::-1])
    ax.set_title("Q7: Mean Absolute Forecast Error by Sector")
    ax.set_xlabel("|Estimate Error|")
    plt.tight_layout()
    plt.savefig("outputs/chart_7_forecast_error.png", dpi=150)
    plt.close()
else:
    log_defect("Q7", "missing_est_error", "Forecast error or actual/estimate columns not found")
    results["Q7"] = {"status": "missing_estimate_error"}

# Q8: Debt ratio vs volatility
if debt_col:
    df[debt_col] = pd.to_numeric(df[debt_col], errors="coerce")
    q10 = df[ret_col].quantile(0.10)
    df["_regime"] = np.where(df[ret_col] <= q10, "Sharp_Drop", "Ordinary")
    sec8_all = df.groupby(sector_col).agg(
        mean_debt=(debt_col, "mean"),
        vol=(ret_col, "std"),
        n=(ret_col, "count"),
    ).dropna()
    sec8_reg = df.groupby([sector_col, "_regime"])[ret_col].std().unstack()
    corr8 = sec8_all["mean_debt"].corr(sec8_all["vol"])
    results["Q8"] = {
        "corr_debt_vol": float(corr8) if pd.notna(corr8) else None,
        "by_sector": sec8_all.join(sec8_reg).to_dict(orient="index"),
    }
    report_lines.append(f"\n--- Q8: Debt-Volatility Correlation={corr8} ---")
    report_lines.append(sec8_all.join(sec8_reg).sort_values("vol", ascending=False).head(15).to_string())

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sec8_all["mean_debt"], sec8_all["vol"])
    for idx, r in sec8_all.iterrows():
        ax.annotate(str(idx)[:12], (r["mean_debt"], r["vol"]), fontsize=8)
    ax.set_title("Q8: Debt Ratio vs Return Volatility")
    ax.set_xlabel("Mean Debt Ratio")
    ax.set_ylabel("Volatility (std)")
    plt.tight_layout()
    plt.savefig("outputs/chart_8_debt_volatility.png", dpi=150)
    plt.close()
else:
    log_defect("Q8", "missing_debt", "Debt ratio column not found")
    results["Q8"] = {"status": "missing_debt_ratio"}

# Q9: PBR < 1 companies
if pbr_col:
    df[pbr_col] = pd.to_numeric(df[pbr_col], errors="coerce")
    low_pbr = df[df[pbr_col] < 1.0]
    cluster9 = low_pbr.groupby(sector_col).size().sort_values(ascending=False)
    roe_summary = {}
    if roe_col:
        df[roe_col] = pd.to_numeric(df[roe_col], errors="coerce")
        lp_roe = low_pbr.copy()
        lp_roe["_roe_sign"] = np.where(lp_roe[roe_col] >= 0, "Positive_ROE", "Negative_ROE")
        roe_summary = lp_roe.groupby("_roe_sign")[ret_col].agg(["count", "mean", "std"]).to_dict(orient="index")
    rec_summary = {}
    if ticker_col:
        pbr_first_last = low_pbr.groupby(ticker_col)[pbr_col].agg(["first", "last"]).dropna()
        pbr_first_last["status"] = np.where(pbr_first_last["last"] >= 1.0, "Recovered_PBR>=1", "Stayed_Low_PBR<1")
        rec_summary = pbr_first_last["status"].value_counts().to_dict()
    results["Q9"] = {
        "n_low_pbr_rows": int(len(low_pbr)),
        "top_sectors_low_pbr": cluster9.head(15).to_dict(),
        "roe_returns_on_low_pbr": roe_summary,
        "pbr_recovery_counts": rec_summary,
    }
    report_lines.append(f"\n--- Q9: PBR < 1 rows={len(low_pbr)}, Recovery={rec_summary} ---")
    report_lines.append("Top sectors (PBR < 1):\n" + cluster9.head(10).to_string())

    fig, ax = plt.subplots(figsize=(9, 5))
    top9 = cluster9.head(12)
    ax.barh(top9.index.astype(str)[::-1], top9.values[::-1])
    ax.set_title("Q9: PBR < 1 Observations by Sector")
    ax.set_xlabel("Observation Count")
    plt.tight_layout()
    plt.savefig("outputs/chart_9_pbr_outcome.png", dpi=150)
    plt.close()
else:
    log_defect("Q9", "missing_pbr", "PBR column not found")
    results["Q9"] = {"status": "missing_pbr"}

defect_df = pd.DataFrame(defects)
defect_df.to_csv("outputs/q5_9_defect_log.csv", index=False)
report_lines.append("\n--- Defect Log ---")
report_lines.append(defect_df.to_string() if len(defect_df) else "No defects found.")

with open("outputs/q5_9_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
with open("outputs/q5_9_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("=== QUESTIONS 5-9 COMPLETED ===")
print("Used file:", panel_path)
print("Available columns:", cols)
print("Defects:", defects)
for p in sorted(glob.glob("outputs/chart_[5-9]_*.png")) + ["outputs/q5_9_report.txt", "outputs/q5_9_results.json"]:
    if os.path.exists(p):
        print("Ready:", p)
