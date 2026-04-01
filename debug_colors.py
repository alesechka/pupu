import csv, re

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

desc_col = headers.index('_DESCRIPTION_')

# Find all unique color values
colors = set()
for r in rows:
    if desc_col < len(r):
        for m in re.finditer(r'\bcolor\s*:\s*[^;"\'>]+', r[desc_col]):
            colors.add(m.group().strip())

print(f"Уникальных color значений: {len(colors)}")
for c in sorted(colors)[:30]:
    print(repr(c))

# Also check what other CSS props exist besides font-family, color
props = {}
for r in rows:
    if desc_col < len(r):
        for m in re.finditer(r'([\w-]+)\s*:', r[desc_col]):
            p = m.group(1)
            props[p] = props.get(p, 0) + 1

print("\nВсе CSS свойства (топ 30):")
for k, v in sorted(props.items(), key=lambda x: -x[1])[:30]:
    print(f"  {k}: {v}")
