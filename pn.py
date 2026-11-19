import glob
import os
import pandas as pd

IN_DIR = "data/daily_q1_q9"
OUT_PATH = "data/panel_q1_q9.csv"

os.makedirs("data", exist_ok=True)
files = sorted(glob.glob(os.path.join(IN_DIR, "*.csv")))

dfs = []
for f in files:
    df = pd.read_csv(f, dtype={"code": str, "financials_json": str})
    dfs.append(df)

panel = pd.concat(dfs, ignore_index=True)

num_cols = [
    "close", "open", "high", "low",
    "volume", "trading_value", "mktcap", "shares",
    "per", "pbr", "eps", "bps", "dividend_yield", "foreign_ownership",
]
for col in num_cols:
    if col in panel.columns:
        panel[col] = pd.to_numeric(panel[col], errors="coerce")

panel = panel.sort_values(["date", "code"]).reset_index(drop=True)
panel.to_csv(OUT_PATH, index=False, encoding="utf-8")

print("\nbarcha yig'ilgan fayllar")
print(f"Birlashtirilgan kunlik CSV fayllar soni: {len(files)}")
print(f"Jami qatorlar soni: {len(panel)}")
print(f"Jami ustunlar soni: {len(panel.columns)}")
print(f"Sana oralig'i: {panel['date'].min()} -> {panel['date'].max()}")
print(f"Saqlangan fayl manzili: {OUT_PATH}")
