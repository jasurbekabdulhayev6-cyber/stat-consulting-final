import glob
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)

csv_candidates = sorted(
    set(glob.glob("**/*.csv", recursive=True)),
    key=lambda p: os.path.getsize(p) if os.path.exists(p) else -1,
    reverse=True,
)
csv_candidates = [
    p for p in csv_candidates
    if "defect_log" not in p
    and "numeric_summary" not in p
    and "raqamli_xulosa" not in p
    and "top_market_cap" not in p
    and "kapitallashuv" not in p
    and "sector_dispersion" not in p
    and "dispersiyasi" not in p
    and "correlation_matrix" not in p
    and "korrelyatsiya" not in p
    and "volume_spikes" not in p
    and "sakrashlari" not in p
]

if csv_candidates:
    data_path = csv_candidates[0]
    df = pd.read_csv(data_path)
    source_label = f"Existing dataset ({data_path})"
else:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-05-01", periods=120)
    sectors = ["Technology", "Finance", "Healthcare", "Energy", "Consumer", "Industrial"]
    tickers = [f"STOCK_{i:02d}" for i in range(1, 25)]

    records = []
    for t_idx, ticker in enumerate(tickers):
        sector = sectors[t_idx % len(sectors)]
        base_mcap = rng.uniform(5.0, 250.0)
        base_vol = rng.uniform(1e5, 5e6)
        returns = rng.normal(0.0004, 0.018, size=len(dates))
        spike_idx = rng.choice(len(dates), size=4, replace=False)
        returns[spike_idx] += rng.choice([-0.08, 0.09], size=4)

        close_price = rng.uniform(20.0, 300.0) * np.cumprod(1.0 + returns)
        mcap_b = base_mcap * (close_price / close_price[0])
        volume = base_vol * rng.lognormal(0.0, 0.45, size=len(dates))
        volume[spike_idx] *= rng.uniform(3.0, 7.0, size=4)
        roe_pct = rng.normal(14.5, 6.0, size=len(dates))
        pe_ratio = np.clip(rng.normal(22.0, 9.0, size=len(dates)), 4.0, 80.0)

        for dt, px, ret, mc, vol, roe_v, pe_v in zip(dates, close_price, returns, mcap_b, volume, roe_pct, pe_ratio):
            records.append({
                "date": dt.strftime("%Y-%m-%d"),
                "ticker": ticker,
                "sector": sector,
                "close_price": round(float(px), 4),
                "daily_return": round(float(ret), 6),
                "market_cap_b": round(float(mc), 4),
                "trading_volume": int(vol),
                "roe_pct": round(float(roe_v), 3),
                "pe_ratio": round(float(pe_v), 3),
            })

    df = pd.DataFrame(records)
    data_path = "data/panel_q5_q9_english.csv"
    df.to_csv(data_path, index=False)
    source_label = f"Generated stock market panel ({data_path})"

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
desc_df = df[num_cols].describe().T
desc_df.to_csv("outputs/q5_9_numeric_summary.csv")

# Q5: Market capitalization
top_mcap = pd.Series(dtype=float)
if "market_cap_b" in df.columns and "ticker" in df.columns:
    top_mcap = df.groupby("ticker")["market_cap_b"].mean().sort_values(ascending=False).head(15)
    top_mcap.to_csv("outputs/q5_top_market_cap.csv")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh(top_mcap.index.astype(str)[::-1], top_mcap.values[::-1])
    ax.set_title("Q5: Average Market Capitalization (Top 15)")
    ax.set_xlabel("Market Capitalization ($B)")
    ax.set_ylabel("Ticker")
    plt.tight_layout()
    plt.savefig("outputs/chart_5_q5.png", dpi=150)
    plt.close()

# Q6: Sector return dispersion
sec_disp = pd.DataFrame()
if "sector" in df.columns and "daily_return" in df.columns:
    sec_disp = df.groupby("sector")["daily_return"].agg(["count", "mean", "std"]).sort_values("std", ascending=False)
    sec_disp.to_csv("outputs/q6_sector_dispersion.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(sec_disp.index.astype(str), sec_disp["std"].values)
    ax.set_title("Q6: Sector Daily Return Volatility (Std Dev)")
    ax.set_xlabel("Sector")
    ax.set_ylabel("Standard Deviation")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig("outputs/chart_6_q6.png", dpi=150)
    plt.close()

# Q7: Correlation matrix
corr_cols = [c for c in ["close_price", "daily_return", "market_cap_b", "trading_volume", "roe_pct", "pe_ratio"] if c in df.columns]
if len(corr_cols) >= 2:
    corr_mat = df[corr_cols].corr()
    corr_mat.to_csv("outputs/q7_correlation_matrix.csv")
    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(corr_mat.values, aspect="auto")
    ax.set_xticks(range(len(corr_mat.columns)))
    ax.set_xticklabels(corr_mat.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(corr_mat.index)))
    ax.set_yticklabels(corr_mat.index)
    ax.set_title("Q7: Financial & Return Correlation Matrix")
    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig("outputs/chart_7_q7.png", dpi=150)
    plt.close()

# Q8: Trading volume spikes
q95_vol = 0.0
if "trading_volume" in df.columns:
    vol_series = df["trading_volume"]
    q95_vol = float(vol_series.quantile(0.95))
    spikes_df = df[df["trading_volume"] >= q95_vol].head(100)
    spikes_df.to_csv("outputs/q8_volume_spikes_top95.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(np.log10(np.maximum(vol_series.values, 1)), bins=35)
    ax.set_title("Q8: Trading Volume Distribution (log10)")
    ax.set_xlabel("log10(Trading Volume)")
    ax.set_ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("outputs/chart_8_q8.png", dpi=150)
    plt.close()

# Q9: Daily return distribution
mean_ret = 0.0
if "daily_return" in df.columns:
    mean_ret = float(df["daily_return"].mean())
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["daily_return"].dropna().values, bins=40)
    ax.set_title("Q9: Daily Return Distribution")
    ax.set_xlabel("Daily Return")
    ax.set_ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("outputs/chart_9_q9.png", dpi=150)
    plt.close()

mean_mcap = float(df["market_cap_b"].mean()) if "market_cap_b" in df.columns else 0.0
top_vol_sector = str(sec_disp.index[0]) if len(sec_disp) > 0 else "N/A"

summary_en = f"""EXECUTIVE SUMMARY — QUESTIONS 5 TO 9 (ENGLISH)

- Data source: {source_label}
- Sample size: {df.shape[0]} rows, {df.shape[1]} columns
- Question 5 (Market Capitalization): Average market cap is ${mean_mcap:.2f}B, with top-ranked stocks driving overall valuation concentration.
- Question 6 (Sector Dispersion): "{top_vol_sector}" exhibits the highest daily return volatility (standard deviation).
- Question 7 (Correlations): Linear relationships across price, daily return, market cap, volume, ROE, and P/E are captured in the correlation matrix.
- Question 8 (Volume Spikes): The 95th percentile volume threshold ({q95_vol:.0f}) isolates high-activity surge events.
- Question 9 (Return Distribution): Mean daily return is {mean_ret:.6f}, with tail events reflecting market shocks and recovery dynamics.
"""

report_en = f"""STATISTICAL CONSULTING REPORT — QUESTIONS 5 TO 9 (FULL ENGLISH)

1. Overview and Data Foundation
This section presents empirical tables and charts for Questions 5 through 9 based on {source_label} ({df.shape[0]} rows and {df.shape[1]} columns).

2. Question 5: Market Capitalization and Rankings
Average market capitalization was computed across tickers to identify the top 15 largest stocks (q5_top_market_cap.csv and chart_5_q5.png).

3. Question 6: Sector Return Dispersion
Daily return count, mean, and standard deviation were calculated per sector, highlighting "{top_vol_sector}" as the most volatile sector (q6_sector_dispersion.csv and chart_6_q6.png).

4. Question 7: Correlation Structure
Pairwise correlations among price, daily return, market cap, trading volume, ROE, and P/E ratio were computed and visualized (q7_correlation_matrix.csv and chart_7_q7.png).

5. Question 8: Trading Volume Spikes
High-volume anomalies above the 95th percentile ({q95_vol:.0f}) were extracted into q8_volume_spikes_top95.csv and visualized via log10 volume distribution (chart_8_q8.png).

6. Question 9: Return Distribution and Recovery Overview
Daily return distribution centers around {mean_ret:.6f}, illustrating dispersion and tail behavior across trading days (chart_9_q9.png).
"""

with open("outputs/q5_9_summary.txt", "w", encoding="utf-8") as f:
    f.write(summary_en.strip() + "\n")

with open("outputs/q5_9_report.txt", "w", encoding="utf-8") as f:
    f.write(report_en.strip() + "\n")

q1_4_candidates = [
    "outputs/q1_q4_unified_report.txt",
    "outputs/yakuniy_1_4_hisobot.txt",
    "outputs/savol4_report.txt",
]
q1_4_text = ""
for path in q1_4_candidates:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            q1_4_text = f.read().strip()
        break
if not q1_4_text:
    q1_4_text = "Questions 1 to 4 analyses and charts are stored under outputs/."

charts_1_4 = sorted(glob.glob("outputs/grafik_*.png"))
charts_5_9 = sorted(glob.glob("outputs/chart_*.png"))

presentation_lines = [
    "# Statistical Consulting Project — Unified Presentation Summary (Questions 1–9)",
    "",
    "**Repository:** `jasurbekabdulhayev6-cyber/stat-consulting-final` (`main`)",
    "",
    "---",
    "",
    "## 1. Executive Summary (Questions 1–9)",
    "",
    "- All analytical scripts, tables, reports, and charts for Questions 1–9 are consolidated inside `stat-consulting-final`.",
    "- **Questions 1–4:** Covers rankings/metrics, sector differences, correlations, and trading volume vs. price relationships.",
    "- **Questions 5–9:** Covers market capitalization, sector return dispersion, financial correlations, volume spikes, and return distribution.",
    "",
    "---",
    "",
    "## 2. Questions 1–4: Summary and Charts",
    "",
]

for chart_path in charts_1_4:
    cname = os.path.basename(chart_path)
    presentation_lines.append(f"- `{cname}`: ![{cname}]({cname})")

presentation_lines += [
    "",
    "```text",
    q1_4_text[:5000],
    "```",
    "",
    "---",
    "",
    "## 3. Questions 5–9: Summary, Report and Charts",
    "",
    "### Executive Summary",
    "",
    "```text",
    summary_en.strip(),
    "```",
    "",
    "### Charts",
    "",
]

for chart_path in charts_5_9:
    cname = os.path.basename(chart_path)
    presentation_lines.append(f"- `{cname}`: ![{cname}]({cname})")

presentation_lines += [
    "",
    "### Detailed Report",
    "",
    "```text",
    report_en.strip(),
    "```",
]

with open("outputs/taqdimot_1_9_jamlanma.md", "w", encoding="utf-8") as f:
    f.write("\n".join(presentation_lines) + "\n")

results_json = {
    "language": "english",
    "rows": int(df.shape[0]),
    "columns": int(df.shape[1]),
    "charts_q5_q9": [os.path.basename(x) for x in charts_5_9],
    "unified_presentation_file": "outputs/taqdimot_1_9_jamlanma.md",
}
with open("outputs/q5_9_empirical_results.json", "w", encoding="utf-8") as f:
    json.dump(results_json, f, indent=2, ensure_ascii=False)

with open("outputs/q5_9_results.json", "w", encoding="utf-8") as f:
    json.dump(results_json, f, indent=2, ensure_ascii=False)

print("DONE: All outputs, charts, summaries, and unified presentation are now in English.")
