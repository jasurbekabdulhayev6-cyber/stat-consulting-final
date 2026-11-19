import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(OUT_DIR, "q1_q4_unified_results.json"), "r", encoding="utf-8") as f:
    q13 = json.load(f)

with open(os.path.join(OUT_DIR, "savol4_results.json"), "r", encoding="utf-8") as f:
    q4 = json.load(f)

# 1-SAVOL GRAFIKI: Sektorlar bo'yicha o'rtacha reyting siljishi (95% CI bilan)
m_df = pd.DataFrame(q13["q1_market_cap_ranking"]["sector_ranking_moves"]).head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("white")
y_pos = np.arange(len(m_df))
x_err = [
    (m_df["mean_abs_rank_move"] - m_df["abs_ci95_low"]).clip(lower=0),
    (m_df["abs_ci95_high"] - m_df["mean_abs_rank_move"]).clip(lower=0),
]
ax.barh(y_pos, m_df["mean_abs_rank_move"], xerr=x_err, capsize=4, color="#2b5c8f", alpha=0.9)
ax.set_yticks(y_pos)
ax.set_yticklabels(m_df["sector"])
ax.set_xlabel("Mean |Rank Change| (95% CI)")
ax.set_title("Q1: Market-Cap Rank Movement by Sector (Top 10)")
ax.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "grafik_1_reyting.png"), dpi=200)
plt.close(fig)

# 2-SAVOL GRAFIKI: Sektorlar jamlanma daromadliligi (Top 10)
c_df = pd.DataFrame(q13["q2_sector_return_gap"]["sector_cumulative_returns_pct"]).head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("white")
ax.barh(c_df["sector"], c_df["cum_return_pct"], color="#2e7d32", alpha=0.9)
ax.set_xlabel("Cumulative Return (%)")
ax.set_title("Q2: Cumulative Return by Sector (Top 10)")
ax.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "grafik_2_sektor_farqi.png"), dpi=200)
plt.close(fig)

# 3-SAVOL GRAFIKI: Keskin tebranish kunlari vs Odatiy kunlar korrelyatsiyasi (95% CI)
s_ci = q13["q3_cross_sector_correlation"]["sharp_market_move_days_corr_ci95"]
o_ci = q13["q3_cross_sector_correlation"]["ordinary_days_corr_ci95"]
fig, ax = plt.subplots(figsize=(8, 5.5))
fig.patch.set_facecolor("white")
labels = ["Sharp Market Days", "Ordinary Days"]
means = [s_ci["mean"], o_ci["mean"]]
yerr = [
    [max(0.0, s_ci["mean"] - s_ci["ci95_low"]), max(0.0, o_ci["mean"] - o_ci["ci95_low"])],
    [max(0.0, s_ci["ci95_high"] - s_ci["mean"]), max(0.0, o_ci["ci95_high"] - o_ci["mean"])],
]
ax.bar(labels, means, yerr=yerr, capsize=6, width=0.45, color=["#c62828", "#455a64"], alpha=0.9)
ax.set_ylabel("Mean Pairwise Correlation (95% CI)")
ax.set_title("Q3: Cross-Sector Correlation — Sharp vs. Ordinary Days")
ax.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "grafik_3_korrelyatsiya.png"), dpi=200)
plt.close(fig)

# 4-SAVOL GRAFIKI: Oldingi (-20..-5) va Keyingi (+5..+20) kunlik o'rtacha daromadlar
base_def = q4["definitions_summary"]["base_med20_ge_2.0x"]
horizons = ["pre_20d_pct", "pre_10d_pct", "pre_5d_pct", "post_5d_pct", "post_10d_pct", "post_20d_pct"]
h_labels = ["-20d", "-10d", "-5d", "+5d", "+10d", "+20d"]
h_means = [base_def[h]["mean"] for h in horizons]
h_low = [base_def[h]["ci95_low"] for h in horizons]
h_high = [base_def[h]["ci95_high"] for h in horizons]

fig, ax = plt.subplots(figsize=(10, 5.5))
fig.patch.set_facecolor("white")
ax.plot(h_labels, h_means, marker="o", linewidth=2, color="#6a1b9a")
ax.fill_between(h_labels, h_low, h_high, color="#6a1b9a", alpha=0.18, label="95% CI")
ax.axvline(2.5, color="#888888", linestyle="--", linewidth=1.2, label="Spike Day (t=0)")
ax.axhline(0.0, color="#000000", linewidth=0.8)
ax.set_xlabel("Trading Day Horizon Relative to Spike")
ax.set_ylabel("Mean Return (%)")
ax.set_title(f"Q4: Pre & Post Spike Return Dynamics ({q4['mode_used']})")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "grafik_4_hajm_narx.png"), dpi=200)
plt.close(fig)

print("=== 4 TA ALOHIDA GRAFIK TAYYOR ===")
for name in ("grafik_1_reyting.png", "grafik_2_sektor_farqi.png", "grafik_3_korrelyatsiya.png", "grafik_4_hajm_narx.png"):
    print(os.path.join(OUT_DIR, name))
