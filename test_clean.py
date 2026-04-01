from clean_description_styles import clean_html
import csv

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

desc_col = headers.index('_DESCRIPTION_')

count = 0
for r in rows:
    if desc_col < len(r) and '<h2' in r[desc_col] and '<img' in r[desc_col]:
        cleaned = clean_html(r[desc_col])
        print(f"=== Example {count+1} ===")
        print(cleaned)
        print()
        count += 1
        if count >= 3:
            break
