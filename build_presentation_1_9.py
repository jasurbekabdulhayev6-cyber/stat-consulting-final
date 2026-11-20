import glob
import os

os.makedirs("outputs", exist_ok=True)

charts_1_4 = sorted(glob.glob("outputs/grafik_*.png"))
charts_5_9 = sorted(glob.glob("outputs/chart_*.png"))

def read_if_exists(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    return f"[{path} fayli topilmadi]"

q1_4_text = read_if_exists("outputs/q1_q4_unified_report.txt")
if q1_4_text.startswith("["):
    q1_4_text = read_if_exists("outputs/yakuniy_1_4_hisobot.txt")

q5_9_summary = read_if_exists("outputs/q5_9_summary.txt")
q5_9_report = read_if_exists("outputs/q5_9_report.txt")
q5_9_emp = read_if_exists("outputs/q5_9_empirical_results.json")

lines = [
    "# Statistical Consulting — 1–9 Savollar Yakuniy Taqdimot Jamlanmasi",
    "",
    "**Repozitoriy:** `jasurbekabdulhayev6-cyber/stat-consulting-final` (`main`)",
    "",
    "---",
    "",
    "## 1. Umumiy Xulosa (Executive Summary — Q1–Q9)",
    "",
    "- Loyiha 1-dan 9-gacha bo‘lgan barcha savollar bo‘yicha tahliliy kodlar, natija jadvallari, hisobotlar va vizual grafiklarni yagona `stat-consulting-final` repozitoriyasida birlashtiradi.",
    "- **Q1–Q4 qismi:** Reyting/ko‘rsatkichlar, sektor farqlari, korrelyatsiya va savdo hajmi–narx bog‘liqligini qamrab oladi.",
    "- **Q5–Q9 qismi:** Bozor kapitallashuvi darajalari, sektor dispersiyasi, moliyaviy va daromad korrelyatsiyasi, savdo hajmi sakrashlari hamda taqsimot/tiklanish dinamikasini tahlil qiladi.",
    "",
    "---",
    "",
    "## 2. Q1–Q4 Savollar: Asosiy Xulosalar va Hisobot",
    "",
    "### Q1–Q4 Grafiklari",
]

if charts_1_4:
    for c in charts_1_4:
        name = os.path.basename(c)
        lines.append(f"- `{name}`: ![{name}]({name})")
else:
    lines.append("- Q1–Q4 PNG grafiklari ro‘yxati aniqlanmadi.")

lines += [
    "",
    "### Q1–Q4 Hisobot Matni",
    "",
    "```text",
    q1_4_text[:6000],
    "```",
    "",
    "---",
    "",
    "## 3. Q5–Q9 Savollar: Summary, Empirik Ko‘rsatkichlar va Hisobot",
    "",
    "### Q5–Q9 Qisqa Xulosa (Summary)",
    "",
    "```text",
    q5_9_summary,
    "```",
    "",
    "### Q5–Q9 Empirik Natijalar (JSON)",
    "",
    "```json",
    q5_9_emp,
    "```",
    "",
    "### Q5–Q9 Grafiklari",
]

if charts_5_9:
    for c in charts_5_9:
        name = os.path.basename(c)
        lines.append(f"- `{name}`: ![{name}]({name})")
else:
    lines.append("- Q5–Q9 PNG grafiklari ro‘yxati aniqlanmadi.")

lines += [
    "",
    "### Q5–Q9 Batafsil Hisobot",
    "",
    "```text",
    q5_9_report[:6000],
    "```",
    "",
    "---",
    "",
    "## 4. Repozitoriy Tuzilmasi (Barcha Fayllar Bitta Joyda)",
    "",
    "- **Skriptlar:** `savollar1-4.py`, `savol4.py`, `grafiklar_1_4.py`, `parse_stock.py`, `pn.py`, `savollar_5_9.py`, `run_full_q5_q9.py`, `build_presentation_1_9.py`",
    "- **Natijalar va grafiklar (`outputs/`):** Q1–Q4 va Q5–Q9 bo‘yicha barcha `.png`, `.csv`, `.json`, `.txt` fayllar hamda ushbu jamlanma `outputs/taqdimot_1_9_jamlanma.md`",
]

out_file = "outputs/taqdimot_1_9_jamlanma.md"
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("YARATILDI:", out_file, "Hajmi (bayt):", os.path.getsize(out_file))
