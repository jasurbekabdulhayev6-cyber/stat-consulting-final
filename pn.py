import glob
import os
import re
from bs4 import BeautifulSoup

folders = sorted(glob.glob('/mnt/data/stock/20*'))
sample_file = sorted(glob.glob(folders[0] + '/*.html'))[0]

with open(sample_file, 'rb') as f:
    raw = f.read()

txt = raw.decode('utf-8', errors='replace')
soup = BeautifulSoup(txt, 'html.parser')

code = os.path.basename(sample_file).replace('.html', '')
name_tag = soup.select_one('.wrap_company h2 a')
name = name_tag.get_text(strip=True) if name_tag else None

# Sektor nomi (업종)
sector = None
for a in soup.select('a[href*="sise_group_detail"]'):
    sector = a.get_text(strip=True)
    break

# Asosiy ko'rsatkichlar (시가총액, PER, PBR va h.k.)
info = {}
for tr in soup.select('table tr'):
    ths = [th.get_text(" ", strip=True) for th in tr.find_all('th')]
    tds = [td.get_text(" ", strip=True) for td in tr.find_all('td')]
    if len(ths) == 1 and len(tds) == 1:
        info[ths[0]] = tds[0]

print("Fayl:", sample_file)
print("Kod:", code, "| Nomi:", name, "| Sektor:", sector)
print("\nTopilgan ko'rsatkichlar:")
for k, v in list(info.items())[:20]:
    print(f"  {k}: {v}")
