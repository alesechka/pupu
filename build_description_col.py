"""
Добавляет колонку "Описание" в CSV файлы.
Колонка содержит:
  - <p><img src="https://promfurnitura.by/image/catalog/prom-furnitura/zamki/ИМЯ.png" style="width: XXXpx;"></p>
    для каждого скрина товара (включая части _part_N)
  - + innerHTML блока #prim (колонка "Применение HTML")

Матчинг скринов к товару: код из URL (последний сегмент пути, до первого _)
сравнивается с началом имени файла скрина (без учёта _ в коде).
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
]


def get_product_code(url: str) -> str:
    """
    Извлекает код товара из URL и нормализует (убирает _).
    URL: .../a40101_003_zamki_.../ → 'a40101003'
    URL: .../a40101_063_a40105_zamki_.../ → 'a40101063a40105'
    Берём токены пока они содержат цифры (коды), стоп на чисто буквенных (транслит).
    """
    parts = [p for p in url.rstrip("/").split("/") if p]
    if not parts:
        return ""
    slug = parts[-1]
    tokens = slug.split("_")
    code_tokens = []
    for t in tokens:
        if re.search(r'[а-яёА-ЯЁ]', t):
            break
        # Стоп если токен чисто буквенный (транслит слова типа 'zamki', 'povorotnye')
        if t.isalpha():
            break
        code_tokens.append(t)
    return "".join(code_tokens).lower()


def get_file_code(filename: str) -> str:
    """
    Извлекает нормализованный код из имени файла скрина.
    'a40101003_замки_..._table_1.png' → 'a40101003'
    'a40101063_a40105_замки_..._table_1.png' → 'a40101063a40105'
    """
    name = Path(filename).stem
    name = re.sub(r'_part_\d+$', '', name)
    tokens = name.split("_")
    code_tokens = []
    for t in tokens:
        if re.search(r'[а-яёА-ЯЁ]', t):
            break
        if t == 'table':
            break
        if t.isalpha():
            break
        code_tokens.append(t)
    return "".join(code_tokens).lower()


def build_screenshot_index() -> dict[str, list[Path]]:
    """
    Строит индекс: нормализованный_код -> список Path скринов.
    Нормализация имени файла: берём всё до первого '_' (или до '_table').
    Также включает части из подпапок (_part_N).
    """
    index: dict[str, list[Path]] = {}

    for dir_name in SCREENSHOT_DIRS:
        d = Path(dir_name)
        if not d.exists():
            continue

        # Файлы в корне папки
        for f in sorted(d.glob("*.png")):
            code = get_file_code(f.name)
            if code:
                index.setdefault(code, []).append(f)

        # Файлы в подпапках (нарезанные части)
        for sub in sorted(d.iterdir()):
            if sub.is_dir():
                for f in sorted(sub.glob("*.png")):
                    code = get_file_code(f.name)
                    if code:
                        index.setdefault(code, []).append(f)

    return index


def get_img_width(path: Path) -> int:
    try:
        with Image.open(path) as img:
            return img.width
    except Exception:
        return 766


def build_description(url: str, prim_html: str, index: dict[str, list[Path]]) -> str:
    code = get_product_code(url)
    screenshots = index.get(code, [])

    # Убираем дубли (один и тот же файл мог попасть из разных папок)
    seen_names = set()
    unique = []
    for f in screenshots:
        if f.name not in seen_names:
            seen_names.add(f.name)
            unique.append(f)

    html_parts = []
    for f in unique:
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
        prim_html = row[prim_idx] if prim_idx >= 0 and prim_idx < len(row) else ""

        desc = build_description(url, prim_html, index)
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
