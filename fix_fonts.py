"""
Заменяет все font-family в колонке "Описание" на 'Open Sans', sans-serif.
Затрагивает все inline style атрибуты во всех тегах.
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
    "alterv_smazka.csv",
    "alterv_makhoviki.csv",
]

OPEN_SANS = "'Open Sans', sans-serif"

def fix_font_family(html: str) -> str:
    """Заменяет любой font-family в style атрибутах на Open Sans."""
    # Заменяем font-family: "..." или font-family: '...' или font-family: word, word
    return re.sub(
        r'font-family\s*:\s*[^;"\'>]+',
        f'font-family: {OPEN_SANS}',
        html
    )

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
        print(f"  {csv_path}: нет колонки Описание, пропускаем")
        return

    desc_idx = headers.index("Описание")
    updated = 0

    for row in rows:
        if desc_idx >= len(row):
            continue
        original = row[desc_idx]
        if not original:
            continue
        fixed = fix_font_family(original)
        if fixed != original:
            row[desc_idx] = fixed
            updated += 1

    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"  {csv_path}: исправлено {updated} строк")


def main():
    print("Исправляю font-family в колонке Описание...")
    for csv_file in CSV_FILES:
        process_csv(csv_file)
    print("\nГотово.")


if __name__ == "__main__":
    main()
