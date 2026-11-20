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
csv_candidates = [p for p in csv_candidates if "defect_log" not in p]

if csv_candidates:
    data_path = csv_candidates[0]
    df = pd.read_csv(data_path)
    source_mode = f"existing_csv:{data_path}"
else:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-05-01", periods=120)
    sectors = ["Tech", "Finance", "Healthcare", "Energy", "Consumer", "Industrial"]
    tickers = [f"STK_{i:02d}" for i in range(1, 25)]

    rows = []
    for t_idx, ticker in enumerate(tickers):
        sector = sectors[t_idx % len(sectors)]
        base_mcap = rng.uniform(5.0, 250.0)
        base_vol = rng.uniform(1e5, 5e6)
        rets = rng.normal(0.0004, 0.018, size=len(dates))
        spike_idx = rng.choice(len(dates), size=4, replace=False)
        rets[spike_idx] += rng.choice([-0.08, 0.09], size=4)

        price = rng.uniform(20.0, 300.0) * np.cumprod(1.0 + rets)
        mcap = base_mcap * (price / price[0])
        volume = base_vol * rng.lognormal(0.0, 0.45, size=len(dates))
        volume[spike_idx] *= rng.uniform(3.0, 7.0, size=4)
        roe = rng.normal(14.5, 6.0, size=len(dates))
        pe = np.clip(rng.normal(22.0, 9.0, size=len(dates)), 4.0, 80.0)

        for d, p, r, mc, vol, r_val, pe_val in zip(dates, price, rets, mcap, volume, roe, pe):
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "ticker": ticker,
                "sector": sector,
                "close": round(float(p), 4),
                "daily_return": round(float(r), 6),
                "market_cap_b": round(float(mc), 4),
                "volume": int(vol),
                "roe_pct": round(float(r_val), 3),
                "pe_ratio": round(float(pe_val), 3),
            })

    df = pd.DataFrame(rows)
    data_path = "data/panel_q5_q9_sample.csv"
    df.to_csv(data_path, index=False)
    source_mode = f"generated_panel:{data_path}"

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = [c for c in df.columns if c not in num_cols]

desc = df[num_cols].describe().T
desc.to_csv("outputs/q5_9_numeric_summary.csv")

# Q5: Market-cap & concentration
if "market_cap_b" in df.columns:
    c5 = "market_cap_b"
    top_mcap = df.groupby(cat_cols[1] if len(cat_cols) > 1 else cat_cols[0])[c5].mean().sort_values(ascending=False).head(15)
    top_mcap.to_csv("outputs/q5_top_market_cap.csv")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh(top_mcap.index.astype(str)[::-1], top_mcap.values[::-1])
    ax.set_title("Q5: Average Market Cap (Top 15)")
    ax.set_xlabel("Market Cap ($B)")
    plt.tight_layout()
    plt.savefig("outputs/chart_5_q5.png", dpi=150)
    plt.close()

# Q6: Sector return dispersion
if "sector" in df.columns and "daily_return" in df.columns:
    sec_disp = df.groupby("sector")["daily_return"].agg(["count", "mean", "std"]).sort_values("std", ascending=False)
    sec_disp.to_csv("outputs/q6_sector_dispersion.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(sec_disp.index.astype(str), sec_disp["std"].values)
    ax.set_title("Q6: Sector Daily Return Volatility (Std Dev)")
    ax.set_xlabel("Sector")
    ax.set_ylabel("Std Dev")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig("outputs/chart_6_q6.png", dpi=150)
    plt.close()

# Q7: Correlation matrix
corr_cols = [c for c in ["close", "daily_return", "market_cap_b", "volume", "roe_pct", "pe_ratio"] if c in df.columns]
if len(corr_cols) >= 2:
    corr = df[corr_cols].corr()
    corr.to_csv("outputs/q7_correlation_matrix.csv")
    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(corr.values, aspect="auto")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index)
    ax.set_title("Q7: Financial & Return Correlation Matrix")
    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig("outputs/chart_7_q7.png", dpi=150)
    plt.close()

# Q8: Volume spikes & outlier returns
if "volume" in df.columns:
    vol_s = df["volume"]
    q95 = vol_s.quantile(0.95)
    spikes = df[df["volume"] >= q95].head(100)
    spikes.to_csv("outputs/q8_volume_spikes_top95.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(np.log10(np.maximum(vol_s.values, 1)), bins=35)
    ax.set_title("Q8: Log10 Trading Volume Distribution")
    ax.set_xlabel("log10(Volume)")
    ax.set_ylabel("Count")
    plt.tight_layout()
    plt.savefig("outputs/chart_8_q8.png", dpi=150)
    plt.close()

# Q9: Return & valuation recovery overview
if "daily_return" in df.columns:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["daily_return"].dropna().values, bins=40)
    ax.set_title("Q9: Daily Return Distribution")
    ax.set_xlabel("Daily Return")
    ax.set_ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("outputs/chart_9_q9.png", dpi=150)
    plt.close()

out_summary = {
    "source_mode": source_mode,
    "rows": int(df.shape[0]),
    "cols": int(df.shape[1]),
    "charts": sorted([f for f in os.listdir("outputs") if f.endswith(".png")]),
    "csv_outputs": sorted([f for f in os.listdir("outputs") if f.endswith(".csv")]),
}
with open("outputs/q5_9_empirical_results.json", "w", encoding="utf-8") as f:
    json.dump(out_summary, f, indent=2, ensure_ascii=False)

print("SUCCESS:", json.dumps(out_summary, ensure_ascii=False))
