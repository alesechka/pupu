import csv, re

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

# Find description column
desc_col = None
for i, h in enumerate(headers):
    if 'описание' in h.lower() or 'description' in h.lower():
        print(f'Колонка {i}: {h}')
        desc_col = i

if desc_col is None:
    print('Колонки описания не найдено')
    print('Заголовки:', headers[:10])
else:
    bad1 = sum(1 for r in rows if desc_col < len(r) and 'Open Sans&quot;' in r[desc_col])
    bad2 = sum(1 for r in rows if desc_col < len(r) and re.search(r"sans-serif;[A-Za-z&]", r[desc_col]))
    has_ff = sum(1 for r in rows if desc_col < len(r) and 'font-family' in r[desc_col])
    print(f'Всего строк: {len(rows)}')
    print(f'Строк с font-family: {has_ff}')
    print(f'Мусор Open Sans&quot;: {bad1}')
    print(f'Мусор sans-serif;X: {bad2}')
    # Show example of bad
    for r in rows:
        if desc_col < len(r) and ('Open Sans&quot;' in r[desc_col] or re.search(r"sans-serif;[A-Za-z&]", r[desc_col])):
            m = re.search(r'font-family[^"\'<]{0,150}', r[desc_col])
            if m:
                print(f'Пример мусора: {m.group()[:150]}')
            break
    # Show example of any font-family
    for r in rows:
        if desc_col < len(r) and 'font-family' in r[desc_col]:
            m = re.search(r'font-family[^;]{0,80}', r[desc_col])
            if m:
                print(f'Пример font-family: {m.group()[:80]}')
            break
