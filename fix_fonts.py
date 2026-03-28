"""
Заменяет все font-family в колонке "Описание" на 'Open Sans', sans-serif.
Работает через разбивку style-атрибутов на CSS-свойства — надёжно убирает мусор.
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
    "alterv_opory.csv",
    "alterv_petli.csv",
    "alterv_rukoyatki2.csv",
    "alterv_ruchki_p.csv",
    "alterv_ruchki_z.csv",
    "alterv_zazhimy.csv",
]

OPEN_SANS = "'Open Sans', sans-serif"


def fix_style_attr(style_value: str) -> str:
    """Fix font-family in a CSS style string by splitting on CSS property boundaries."""
    props = re.split(r';\s*(?=[\w-]+\s*:)', style_value)
    result = []
    for prop in props:
        prop = prop.strip().rstrip(';')
        if re.match(r'font-family\s*:', prop):
            result.append(f'font-family: {OPEN_SANS}')
        else:
            result.append(prop)
    return '; '.join(result)


def fix_font_family(html: str) -> str:
    """Fix font-family in all style attributes."""
    html = re.sub(r'style="([^"]*)"', lambda m: 'style="' + fix_style_attr(m.group(1)) + '"', html)
    html = re.sub(r"style='([^']*)'", lambda m: "style='" + fix_style_attr(m.group(1)) + "'", html)
    return html


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
