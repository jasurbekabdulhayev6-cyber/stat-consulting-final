import json
import os
import re
import numpy as np
import pandas as pd

PANEL_PATH = "data/panel_q1_q9.csv"
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

WS_RE = re.compile(r"\s+")
USE_COLS = ["date", "code", "name", "sector", "close", "volume", "trading_value", "mktcap"]

df = pd.read_csv(
    PANEL_PATH,
    usecols=lambda c: c in USE_COLS,
    dtype={"code": str, "name": str, "sector": str, "date": str},
)

for col in ("close", "volume", "trading_value", "mktcap"):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["sector_clean"] = (
    df["sector"]
    .fillna("Unknown_Sector")
    .map(lambda x: WS_RE.sub(" ", str(x)).strip() or "Unknown_Sector")
)
df["name_clean"] = df["name"].fillna("").map(lambda x: WS_RE.sub(" ", str(x)).strip())
df = df.sort_values(["code", "date"], kind="mergesort").reset_index(drop=True)

valid_close = df["close"].notna() & (df["close"] > 0)
valid_vol = df["volume"].notna() & (df["volume"] > 0)
valid_tv = df["trading_value"].notna() & (df["trading_value"] > 0)

defect_rows = [
    {
        "field": "close",
        "total_rows": int(len(df)),
        "valid_positive_rows": int(valid_close.sum()),
        "missing_or_nonpos_rows": int((~valid_close).sum()),
    },
    {
        "field": "volume",
        "total_rows": int(len(df)),
        "valid_positive_rows": int(valid_vol.sum()),
        "missing_or_nonpos_rows": int((~valid_vol).sum()),
    },
    {
        "field": "trading_value",
        "total_rows": int(len(df)),
        "valid_positive_rows": int(valid_tv.sum()),
        "missing_or_nonpos_rows": int((~valid_tv).sum()),
    },
]
defect_df = pd.DataFrame(defect_rows)
defect_csv = os.path.join(OUT_DIR, "savol4_defect_log.csv")
defect_df.to_csv(defect_csv, index=False, encoding="utf-8")


def ci95_mean(arr):
    s = pd.Series(arr, dtype="float64").dropna()
    n = int(len(s))
    if n == 0:
        return {"mean": None, "ci95_low": None, "ci95_high": None, "n": 0}
    if n == 1:
        v = float(s.iloc[0])
        return {"mean": v, "ci95_low": v, "ci95_high": v, "n": 1}
    mean = float(s.mean())
    margin = float(1.96 * s.std(ddof=1) / np.sqrt(n))
    return {"mean": mean, "ci95_low": mean - margin, "ci95_high": mean + margin, "n": n}


p_df = df[valid_close].copy()
p_df["ret"] = p_df.groupby("code", sort=False)["close"].pct_change()
p_df = p_df[p_df["ret"].isna() | ((p_df["ret"] >= -0.90) & (p_df["ret"] <= 1.00))].copy()

g_code = p_df.groupby("code", sort=False)
g_close = p_df.groupby("code", sort=False)["close"]

for h in (5, 10, 20):
    p_df[f"post_{h}d_pct"] = (g_close.shift(-h) / p_df["close"] - 1.0) * 100.0
    p_df[f"pre_{h}d_pct"] = (p_df["close"] / g_close.shift(h) - 1.0) * 100.0

# Choose activity series: volume -> trading_value -> abs_return fallback
if int(valid_vol.sum()) >= 100:
    activity_col = "volume"
    mode_used = "volume_spike"
elif int(valid_tv.sum()) >= 100:
    activity_col = "trading_value"
    mode_used = "trading_value_proxy_spike"
else:
    p_df["abs_ret_proxy"] = p_df["ret"].abs()
    activity_col = "abs_ret_proxy"
    mode_used = "abs_return_fallback_spike"

act_series = pd.to_numeric(p_df[activity_col], errors="coerce")
p_df["act_val"] = act_series
act_valid = p_df[p_df["act_val"].notna() & (p_df["act_val"] > 0)].copy()

g_act = act_valid.groupby("code", sort=False)["act_val"]
act_valid["act_med20"] = g_act.transform(lambda s: s.rolling(20, min_periods=5).median().shift(1))
act_valid["act_mean20"] = g_act.transform(lambda s: s.rolling(20, min_periods=5).mean().shift(1))
act_valid["ratio_med20"] = act_valid["act_val"] / act_valid["act_med20"]
act_valid["ratio_mean20"] = act_valid["act_val"] / act_valid["act_mean20"]

defs = [
    ("base_med20_ge_2.0x", act_valid["ratio_med20"] >= 2.0),
    ("alt_med20_ge_1.5x", act_valid["ratio_med20"] >= 1.5),
    ("alt_med20_ge_3.0x", act_valid["ratio_med20"] >= 3.0),
    ("alt_mean20_ge_2.0x", act_valid["ratio_mean20"] >= 2.0),
]

summary_by_def = {}
for name_def, mask in defs:
    sub = act_valid[mask]
    summary_by_def[name_def] = {
        "pre_5d_pct": ci95_mean(sub["pre_5d_pct"]),
        "pre_10d_pct": ci95_mean(sub["pre_10d_pct"]),
        "pre_20d_pct": ci95_mean(sub["pre_20d_pct"]),
        "post_5d_pct": ci95_mean(sub["post_5d_pct"]),
        "post_10d_pct": ci95_mean(sub["post_10d_pct"]),
        "post_20d_pct": ci95_mean(sub["post_20d_pct"]),
    }

top30_spikes = (
    act_valid[act_valid["ratio_med20"] >= 2.0]
    .dropna(subset=["post_20d_pct"])
    .sort_values("ratio_med20", ascending=False, kind="mergesort")
    .head(30)[[
        "date", "code", "name_clean", "sector_clean", "act_val", "ratio_med20",
        "pre_5d_pct", "post_5d_pct", "post_10d_pct", "post_20d_pct",
    ]]
    .rename(columns={"name_clean": "name", "sector_clean": "sector"})
    .reset_index(drop=True)
)
top30_spikes.insert(0, "rank", top30_spikes.index + 1)

out_obj = {
    "mode_used": mode_used,
    "activity_column": activity_col,
    "defect_log": defect_rows,
    "definitions_summary": summary_by_def,
    "top30_spikes_base_med20_2x": top30_spikes.to_dict(orient="records"),
}

json_path = os.path.join(OUT_DIR, "savol4_results.json")
with open(json_path, "w", encoding="utf-8") as jf:
    json.dump(out_obj, jf, ensure_ascii=False, indent=2)

txt_path = os.path.join(OUT_DIR, "savol4_report.txt")
with open(txt_path, "w", encoding="utf-8") as tf:
    tf.write("=== QUESTION 4 UNIFIED REPORT (WITH DEFECT LOG & CI95) ===\n")
    tf.write(f"Mode used: {mode_used} | Activity column: {activity_col}\n\n")
    tf.write("--- DEFECT LOG ---\n" + defect_df.to_string(index=False) + "\n\n")
    for k, v in summary_by_def.items():
        tf.write(f"[{k}]\n")
        for h_key in ("pre_5d_pct", "pre_10d_pct", "pre_20d_pct", "post_5d_pct", "post_10d_pct", "post_20d_pct"):
            st = v[h_key]
            m_str = f"{st['mean']:+.3f}%" if st["mean"] is not None else "N/A"
            lo_str = f"{st['ci95_low']:+.3f}" if st["ci95_low"] is not None else "N/A"
            hi_str = f"{st['ci95_high']:+.3f}" if st["ci95_high"] is not None else "N/A"
            tf.write(f"  {h_key:12s}: mean={m_str} [{lo_str}, {hi_str}] (n={st['n']})\n")
    tf.write("\n[Top 30 Spikes (base_med20_ge_2.0x)]\n" + top30_spikes.to_string(index=False) + "\n")

print("=== QUESTION 4 ANALYSIS COMPLETE ===")
print(f"Mode used: {mode_used} ({activity_col})")
print(f"Report TXT: {txt_path}")
print(f"Results JSON: {json_path}")
print(f"Defect log CSV: {defect_csv}")
