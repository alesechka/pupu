import csv

f = 'product_export_0-100000_2026-03-25-0014.csv'
with open(f, encoding='utf-8-sig') as fh:
    reader = csv.reader(fh, delimiter=';')
    headers = next(reader)
    rows = list(reader)

# Check _CATEGORY_ column - it has the path already!
cat_idx = headers.index('_CATEGORY_')
name_idx = headers.index('_NAME_')
model_idx = headers.index('_MODEL_')
id_idx = headers.index('_ID_')

print("Примеры _CATEGORY_:")
for r in rows[:5]:
    print(f"  ID={r[id_idx]}, MODEL={r[model_idx]}")
    print(f"  CATEGORY={r[cat_idx]}")
    print(f"  NAME={r[name_idx][:80]}")
    print()
