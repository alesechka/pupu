import csv

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

print("Заголовки:")
for i, h in enumerate(headers):
    print(f"  {i}: {h}")

print(f"\nВсего строк: {len(rows)}")
print("\nПример строки (первые 5 колонок):")
for r in rows[:3]:
    print([r[i] if i < len(r) else '' for i in range(min(6, len(headers)))])
