import csv, re

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

desc_col = headers.index('_DESCRIPTION_')

# Find a row with garbage
for r in rows:
    if desc_col < len(r) and 'Open Sans&quot;' in r[desc_col]:
        html = r[desc_col]
        # Find all font-family occurrences
        # Show raw context around font-family - first occurrence
        idx = html.find('Open Sans&quot;')
        if idx >= 0:
            chunk = html[max(0,idx-30):idx+100]
            print(repr(chunk))
        break
