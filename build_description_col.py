"""
Добавляет колонку "Описание" в CSV файлы.
Колонка содержит:
  - <p><img src="https://promfurnitura.by/image/catalog/prom-furnitura/zamki/ИМЯ.png" style="width: XXXpx;"></p>
    для каждого скрина товара (включая части _part_N)
  - + innerHTML блока #prim (колонка "Применение HTML")

Матчинг скринов к товару: по slugify(Категория) — полному названию категории,
совпадающему с началом имени файла скрина.
"""

import csv
import re
import os
from pathlib import Path
from PIL import Image

IMG_BASE_URL = "https://promfurnitura.by/image/catalog/prom-furnitura/zamki/"

SCREENSHOT_DIRS = [
    "table_screenshots_clean",
    "table_screenshots_zamki",
    "table_screenshots_fiksatory",
    "table_screenshots_zashchelki",
    "table_screenshots",
    "table_screenshots_no_favorites",
]

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


def slugify(text: str) -> str:
    """Повторяет логику slugify из screenshot_*.py скриптов."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text)
    return text[:60]


def get_file_slug(filename: str) -> str:
    """
    Извлекает slug из имени файла скрина — всё до '_table_N' (и '_part_N').
    '150_скобы_стяжные_для_регулируемых_защелок_table_1.png' → '150_скобы_стяжные_для_регулируемых_защелок'
    """
    name = Path(filename).stem
    name = re.sub(r'_part_\d+$', '', name)
    name = re.sub(r'_table_\d+$', '', name)
    return name


def build_screenshot_index() -> dict[str, list[Path]]:
    """
    Строит индекс: slug_категории -> список Path скринов.
    Каждый slug берётся только из первой папки в SCREENSHOT_DIRS где он найден —
    чтобы не дублировать файлы из table_screenshots_clean + table_screenshots + etc.
    """
    index: dict[str, list[Path]] = {}

    for dir_name in SCREENSHOT_DIRS:
        d = Path(dir_name)
        if not d.exists():
            continue

        # Собираем все файлы из этой папки (включая подпапки _part_N)
        dir_files: dict[str, list[Path]] = {}
        for f in sorted(d.glob("*.png")):
            slug = get_file_slug(f.name)
            if slug:
                dir_files.setdefault(slug, []).append(f)
        for sub in sorted(d.iterdir()):
            if sub.is_dir():
                for f in sorted(sub.glob("*.png")):
                    slug = get_file_slug(f.name)
                    if slug:
                        dir_files.setdefault(slug, []).append(f)

        # Добавляем в индекс только те slugи, которых ещё нет
        for slug, files in dir_files.items():
            if slug not in index:
                index[slug] = files

    return index


def find_screenshots(category: str, index: dict[str, list[Path]]) -> list[Path]:
    """
    Ищет скрины по slugify(category) — точный матч.
    """
    slug = slugify(category)
    files = index.get(slug, [])
    return sorted(set(files), key=lambda f: f.name)


def get_img_width(path: Path) -> int:
    try:
        with Image.open(path) as img:
            return img.width
    except Exception:
        return 766


def build_description(category: str, prim_html: str, index: dict[str, list[Path]]) -> str:
    screenshots = find_screenshots(category, index)

    html_parts = []
    for f in screenshots:
        width = get_img_width(f)
        img_url = IMG_BASE_URL + f.name
        html_parts.append(f'<p><img src="{img_url}" style="width: {width}px;"></p>')

    if prim_html:
        html_parts.append(prim_html)

    return "".join(html_parts)


def process_csv(csv_path: str, index: dict[str, list[Path]]):
    p = Path(csv_path)
    if not p.exists():
        print(f"  Не найден: {csv_path}")
        return

    with open(p, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        headers = next(reader)
        rows = list(reader)

    # Определяем индексы нужных колонок
    url_idx = headers.index("URL товара") if "URL товара" in headers else 1
    cat_idx = headers.index("Категория") if "Категория" in headers else 0
    prim_idx = headers.index("Применение HTML") if "Применение HTML" in headers else -1

    # Добавляем колонку если её ещё нет
    if "Описание" not in headers:
        headers.append("Описание")
        desc_idx = len(headers) - 1
    else:
        desc_idx = headers.index("Описание")

    updated = 0
    for row in rows:
        # Дополняем строку до нужной длины
        while len(row) < len(headers):
            row.append("")

        url = row[url_idx] if url_idx < len(row) else ""
        category = row[cat_idx] if cat_idx < len(row) else ""
        prim_html = row[prim_idx] if prim_idx >= 0 and prim_idx < len(row) else ""

        desc = build_description(category, prim_html, index)
        row[desc_idx] = desc
        if desc:
            updated += 1

    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"  {csv_path}: обновлено {updated}/{len(rows)} строк")


def main():
    print("Строю индекс скринов...")
    index = build_screenshot_index()
    total = sum(len(v) for v in index.values())
    print(f"  Найдено кодов: {len(index)}, файлов: {total}")

    print("\nОбновляю CSV...")
    for csv_file in CSV_FILES:
        process_csv(csv_file, index)

    print("\nГотово.")


if __name__ == "__main__":
    main()
