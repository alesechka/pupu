import csv, re

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

desc_col = headers.index('_DESCRIPTION_')

# Find a row with garbage and show raw context
for r in rows:
    if desc_col < len(r) and 'Open Sans&quot;' in r[desc_col]:
        html = r[desc_col]
        # Find the garbage
        idx = html.find('Open Sans&quot;')
        chunk = html[max(0,idx-60):idx+80]
        print("Context around garbage:")
        print(repr(chunk))
        print()
        # Check if style= pattern matches
        styles = re.findall(r'style=(["\'])([^"\']*?)\1', html)
        print(f"style= matches with quotes: {len(styles)}")
        # Check style without quotes
        styles2 = re.findall(r'style="([^"]*)"', html)
        print(f'style="..." matches: {len(styles2)}')
        # Check what's around the garbage
        idx2 = html.find('font-family', idx-50)
        if idx2 >= 0:
            print("font-family context:", repr(html[idx2:idx2+150]))
        break
