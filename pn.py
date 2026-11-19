import csv
import glob
import os
import re
from bs4 import BeautifulSoup

os.makedirs('data/daily', exist_ok=True)
os.makedirs('logs', exist_ok=True)

folders = sorted(glob.glob('/mnt/data/stock/20*'))
defect_file = 'logs/defect_log_q1_q4.csv'
write_header = not os.path.exists(defect_file)

with open(defect_file, 'a', newline='', encoding='utf-8') as df_out:
    defect_writer = csv.writer(df_out)
    if write_header:
        defect_writer.writerow(['date', 'file', 'code', 'defect_type', 'detail'])

    for idx, folder in enumerate(folders, start=1):
        date_str = os.path.basename(folder)
        out_csv = f'data/daily/{date_str}.csv'

        if os.path.exists(out_csv):
            if idx % 50 == 0 or idx == len(folders):
                print(f"[{idx}/{len(folders)}] {date_str}: avval tayyorlangan (o'tkazildi).")
            continue

        html_files = sorted(glob.glob(folder + '/*.html'))
        rows_out = []

        for fpath in html_files:
            fname = os.path.basename(fpath)
            m_code = re.search(r'_(\d{6})\.html$', fname)
            code = m_code.group(1) if m_code else fname.replace('.html', '')

            try:
                with open(fpath, 'rb') as f:
                    raw = f.read()

                if len(raw) < 500:
                    defect_writer.writerow([date_str, fname, code, 'EMPTY_OR_TINY_FILE', f'size={len(raw)}'])
                    continue

                txt = None
                for enc in ['cp949', 'euc-kr', 'utf-8']:
                    try:
                        txt = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue

                if txt is None:
                    txt = raw.decode('cp949', errors='replace')
                    defect_writer.writerow([date_str, fname, code, 'ENCODING_REPLACE', 'cp949 fallback'])

                soup = BeautifulSoup(txt, 'html.parser')

                name_tag = soup.select_one('.wrap_company h2 a')
                name = name_tag.get_text(strip=True) if name_tag else ''

                sec_tag = soup.select_one('a[href*="sise_group_detail"]')
                sector = sec_tag.get_text(strip=True) if sec_tag else ''

                close_tag = soup.select_one('.no_today .blind')
                close_val = re.sub(r'[^\d.]', '', close_tag.get_text()) if close_tag else ''

                vol_val = ''
                for td in soup.select('table.no_info td'):
                    if '거래량' in td.get_text(" ", strip=True):
                        b = td.select_one('.blind')
                        if b:
                            vol_val = re.sub(r'[^\d]', '', b.get_text())
                            break

                mktcap_val = ''
                for tr in soup.select('table tr'):
                    th = tr.find('th')
                    td = tr.find('td')
                    if not th or not td:
                        continue
                    if '시가총액' in th.get_text(" ", strip=True):
                        mktcap_val = re.sub(r'[^\d]', '', td.get_text(" ", strip=True))
                        break

                if not close_val:
                    defect_writer.writerow([date_str, fname, code, 'MISSING_CLOSE', name])
                if not sector:
                    defect_writer.writerow([date_str, fname, code, 'MISSING_SECTOR', name])
                if not mktcap_val:
                    defect_writer.writerow([date_str, fname, code, 'MISSING_MKTCAP', name])

                rows_out.append([date_str, code, name, sector, close_val, mktcap_val, vol_val])

            except Exception as e:
                defect_writer.writerow([date_str, fname, code, 'PARSE_EXCEPTION', str(e)[:120]])

        with open(out_csv, 'w', newline='', encoding='utf-8') as f_csv:
            w = csv.writer(f_csv)
            w.writerow(['date', 'code', 'name', 'sector', 'close', 'mktcap', 'volume'])
            w.writerows(rows_out)

        if idx % 20 == 0 or idx == len(folders):
            print(f"[{idx}/{len(folders)}] {date_str}: {len(rows_out)}/{len(html_files)} ta saqlandi.")

saved_files = sorted(glob.glob('data/daily/*.csv'))
print("\n=== YAKUN ===")
print("Jami papkalar:", len(folders))
print("Tayyor CSV kunlar:", len(saved_files))
if saved_files:
    print("Sana oralig'i:", os.path.basename(saved_files[0])[:-4], "->", os.path.basename(saved_files[-1])[:-4])
