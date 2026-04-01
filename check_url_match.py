import csv

# Check alterv CSV for URL format
with open('alterv_vibroopory.csv', encoding='utf-8-sig') as f:
    r = csv.reader(f, delimiter=';')
    h = next(r)
    rows = list(r)

url_idx = h.index('URL товара')
cat_idx = h.index('Категория')
# Find artikul column
print("Колонки alterv_vibroopory.csv:", h[:10])
print()
for row in rows[:3]:
    print("URL:", row[url_idx])
    print("Категория:", row[cat_idx])
    print()

# Check export CSV
with open('product_export_0-100000_2026-03-25-0014.csv', encoding='utf-8-sig') as f:
    r = csv.reader(f, delimiter=';')
    h2 = next(r)
    rows2 = list(r)

print("Колонки export:", h2)
print()
for row in rows2[:3]:
    print("ID:", row[0], "MODEL:", row[4], "MAIN_CAT:", row[1][:60])
    print()
