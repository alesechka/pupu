"""
Заменяет <a ...>текст</a> на просто текст в колонке "Описание" всех CSV.
"""

import csv
import re
from pathlib import Path

CSV_FILES = [
    "alterv_zamki.csv",
    "alterv_all.csv",
    "alterv_vibroopory.csv",
    "alterv_dempfery.csv",
    "alterv_rukoyatki.csv",
    "alterv_rychagi.csv",
    "alterv_fiksatory.csv",
    "alterv_zashchelki.csv",
]


def strip_links(html: str) -> str:
    return re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', html, flags=re.DOTALL)


def process_csv(csv_path: str):
    p = Path(csv_path)
    if not p.exists():
        print(f"  Не найден: {csv_path}")
        return

    with open(p, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        headers = next(reader)
        rows = list(reader)

    if "Описание" not in headers:
        print(f"  {csv_path}: нет колонки 'Описание', пропускаем")
        return

    desc_idx = headers.index("Описание")
    updated = 0
    for row in rows:
        if len(row) <= desc_idx:
            continue
        original = row[desc_idx]
        cleaned = strip_links(original)
        if cleaned != original:
            row[desc_idx] = cleaned
            updated += 1

    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"  {csv_path}: обновлено {updated} строк")


def main():
    for csv_file in CSV_FILES:
        process_csv(csv_file)
    print("Готово.")


if __name__ == "__main__":
    main()
