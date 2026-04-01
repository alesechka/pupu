import csv, re

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

desc_col = headers.index('_DESCRIPTION_')

# Find a row with garbage and show the style= attribute context
for r in rows:
    if desc_col < len(r) and 'Open Sans&quot;' in r[desc_col]:
        html = r[desc_col]
        idx = html.find('Open Sans&quot;')
        # Find the style= before this
        style_start = html.rfind('style=', 0, idx)
        if style_start >= 0:
            chunk = html[style_start:style_start+300]
            print("style= context:")
            print(repr(chunk[:300]))
        break
