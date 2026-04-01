"""Убирает <a href="...">текст</a> из колонки Описание во всех CSV, оставляет только текст."""
import csv, re
from pathlib import Path

FILES = [
    "alterv_opory.csv",
    "alterv_petli.csv",
    "alterv_rukoyatki2.csv",
    "alterv_ruchki_p.csv",
]

for fname in FILES:
    p = Path(fname)
    if not p.exists():
        print(f"Не найден: {fname}")
        continue
    with open(p, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        headers = next(reader)
        rows = list(reader)
    if "Описание" not in headers:
        print(f"{fname}: нет колонки Описание")
        continue
    idx = headers.index("Описание")
    updated = 0
    for row in rows:
        if idx < len(row) and row[idx]:
            fixed = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', row[idx], flags=re.DOTALL)
            if fixed != row[idx]:
                row[idx] = fixed
                updated += 1
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"{fname}: исправлено {updated} строк")
