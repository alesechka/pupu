import csv, re
from pathlib import Path

f = Path("alterv_opory.csv")
with open(f, encoding="utf-8-sig") as fh:
    reader = csv.reader(fh, delimiter=";")
    headers = next(reader)
    rows = list(reader)

idx = headers.index("Описание")
updated = 0
for row in rows:
    if idx < len(row) and row[idx]:
        fixed = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', row[idx], flags=re.DOTALL)
        if fixed != row[idx]:
            row[idx] = fixed
            updated += 1

with open(f, "w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh, delimiter=";")
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Исправлено строк: {updated}")
