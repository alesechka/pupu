"""
Заменяет все font-family в колонке _DESCRIPTION_ на 'Open Sans', sans-serif.
Работает через разбивку style-атрибутов на CSS-свойства — надёжно убирает мусор.
"""

import csv
import re
from pathlib import Path

EXPORT_FILE = "product_export_0-100000_2026-03-25-0014.csv"
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
    def fix_style(m):
        quote = m.group(1)
        style_val = m.group(2)
        fixed = fix_style_attr(style_val)
        return f'style={quote}{fixed}{quote}'
    # Match style="..." allowing single quotes inside double-quoted value and vice versa
    html = re.sub(r'style="([^"]*)"', lambda m: 'style="' + fix_style_attr(m.group(1)) + '"', html)
    html = re.sub(r"style='([^']*)'", lambda m: "style='" + fix_style_attr(m.group(1)) + "'", html)
    return html


def main():
    p = Path(EXPORT_FILE)
    if not p.exists():
        print(f"Файл не найден: {EXPORT_FILE}")
        return

    print(f"Читаю {EXPORT_FILE}...")
    with open(p, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        headers = next(reader)
        rows = list(reader)

    if "_DESCRIPTION_" not in headers:
        print("Колонка _DESCRIPTION_ не найдена!")
        print("Колонки:", headers)
        return

    desc_idx = headers.index("_DESCRIPTION_")
    updated = 0

    for row in rows:
        if desc_idx >= len(row) or not row[desc_idx]:
            continue
        fixed = fix_font_family(row[desc_idx])
        if fixed != row[desc_idx]:
            row[desc_idx] = fixed
            updated += 1

    print(f"Исправлено строк: {updated}/{len(rows)}")

    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print("Готово.")


if __name__ == "__main__":
    main()
