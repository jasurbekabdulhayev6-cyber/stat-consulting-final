import glob
import os
import re

folders = sorted(glob.glob('/mnt/data/stock/20*'))
files_day1 = sorted(glob.glob(folders[0] + '/*.html'))
print("Fayllar soni (1-kunda):", len(files_day1))

sample_file = files_day1[0]
with open(sample_file, 'rb') as f:
    raw = f.read()

for enc in ['cp949', 'euc-kr', 'utf-8']:
    try:
        txt = raw.decode(enc)
        print("Ishlagan kodirovka:", enc)
        break
    except UnicodeDecodeError:
        continue

tables = re.findall(r'<table\b.*?</table>', txt, re.I | re.S)
print("Sahifadagi jadvallar soni:", len(tables))

for idx, tbl in enumerate(tables):
    rows = re.findall(r'<tr\b.*?</tr>', tbl, re.I | re.S)
    print(f"\n--- Jadval #{idx+1} (qatorlar: {len(rows)}) ---")
    for r in rows[:6]:
        cells = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip()
                 for c in re.findall(r'<t[dh]\b.*?</t[dh]>', r, re.I | re.S)]
        cells = [c for c in cells if c]
        if cells:
            print("  ", " | ".join(cells)[:110])
