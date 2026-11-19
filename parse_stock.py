import glob
import os
import re

folders = sorted(glob.glob('/mnt/data/stock/20*'))
print("Kunlik papkalar soni:", len(folders))
print("Birinchi va oxirgi sana:", os.path.basename(folders[0]), "->", os.path.basename(folders[-1]))

sample_file = sorted(glob.glob(folders[0] + '/*.html'))[0]
with open(sample_file, errors='ignore') as f:
    txt = f.read()

rows = re.findall(r'<tr\b.*?</tr>', txt, re.I | re.S)
print("\nNamuna fayl:", sample_file)
for r in rows[:15]:
    clean = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', r)).strip()
    if clean:
        print(" ->", clean[:110])
