"""
Делает скриншоты таблиц для товаров у которых нет скринов в папках.
Использует ту же логику что screenshot_zamki.py (clean вариант).
Результат кладёт в table_screenshots_zamki/ (или соответствующую папку).
"""

import os
import re
import csv
import time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://alterv.ru"

SCREENSHOT_DIRS = [
    "table_screenshots_clean",
    "table_screenshots_zamki",
    "table_screenshots_fiksatory",
    "table_screenshots",
    "table_screenshots_no_favorites",
]

# CSV → папка куда класть скрины
CSV_TO_DIR = {
    "alterv_zamki.csv": "table_screenshots_zamki",
    "alterv_all.csv": "table_screenshots_clean",
    "alterv_vibroopory.csv": "table_screenshots_clean",
    "alterv_dempfery.csv": "table_screenshots_clean",
    "alterv_rukoyatki.csv": "table_screenshots_clean",
    "alterv_rychagi.csv": "table_screenshots_clean",
    "alterv_fiksatory.csv": "table_screenshots_fiksatory",
}

CUT_FROM_COLS = {"наличие", "наличие, шт"}

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin: 0; padding: 16px; background: #fff; font-family: Arial, sans-serif; font-size: 13px; }}
  table {{ border-collapse: collapse; white-space: nowrap; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
  thead th {{ background: #f0f0f0; font-weight: bold; }}
  tr:nth-child(even) {{ background: #fafafa; }}
</style>
</head>
<body>
{table_html}
</body>
</html>"""


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text)
    return text[:60]


def get_product_code(url: str) -> str:
    parts = [p for p in url.rstrip("/").split("/") if p]
    if not parts:
        return ""
    slug = parts[-1]
    tokens = slug.split("_")
    code_tokens = []
    for t in tokens:
        if re.search(r"[а-яёА-ЯЁ]", t):
            break
        if t.isalpha():
            break
        code_tokens.append(t)
    return "".join(code_tokens).lower()


def get_file_code(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"_part_\d+$", "", name)
    tokens = name.split("_")
    code_tokens = []
    for t in tokens:
        if re.search(r"[а-яёА-ЯЁ]", t):
            break
        if t == "table":
            break
        if t.isalpha():
            break
        code_tokens.append(t)
    return "".join(code_tokens).lower()


def build_existing_index() -> set:
    """Возвращает множество кодов для которых уже есть скрины."""
    codes = set()
    for d in SCREENSHOT_DIRS:
        p = Path(d)
        if not p.exists():
            continue
        for f in p.glob("*.png"):
            c = get_file_code(f.name)
            if c:
                codes.add(c)
    return codes


def find_missing() -> list[tuple[str, str, str]]:
    """Возвращает список (url, title_slug, out_dir) для товаров без скринов."""
    existing = build_existing_index()
    missing = []
    seen_urls = set()

    for csv_file, out_dir in CSV_TO_DIR.items():
        p = Path(csv_file)
        if not p.exists():
            continue
        with open(p, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f, delimiter=";"))

        url_idx = 1
        cat_idx = 0
        for row in rows[1:]:
            url = row[url_idx] if len(row) > url_idx else ""
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            code = get_product_code(url)
            if code and code not in existing:
                title = row[cat_idx] if len(row) > cat_idx else code
                missing.append((url, title, out_dir))

    return missing


def get_col_text(th) -> str:
    span = th.find("span", class_="flt-table__title")
    raw = span.get_text(strip=True) if span else th.get_text(strip=True)
    return raw.lower()


def clean_table(table) -> None:
    for tfoot in table.find_all("tfoot"):
        tfoot.decompose()
    for tr in table.find_all("tr"):
        if "сбросить фильтр" in tr.get_text(strip=True).lower():
            tr.decompose()

    for el in table.select(".favorites, .fav, .in-favorites, .add-to-favorites, "
                           "[class*='favorit'], [class*='wishlist'], [class*='heart']"):
        el.decompose()
    for el in table.find_all(["a", "button", "span", "div"]):
        if "в избранное" in el.get_text(strip=True).lower():
            el.decompose()

    thead = table.find("thead")
    if not thead:
        return
    headers = thead.find_all("th")
    cut_index = None
    for i, th in enumerate(headers):
        if get_col_text(th) in CUT_FROM_COLS:
            cut_index = i
            break
    if cut_index is None:
        return
    for th in headers[cut_index:]:
        th.decompose()
    tbody = table.find("tbody")
    if not tbody:
        return
    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        for td in cells[cut_index:]:
            td.decompose()


def _hide_popup(page):
    try:
        page.evaluate("""
            ['altasib_geobase_window','altasib_geobase_window_block'].forEach(id => {
                var el = document.getElementById(id); if (el) el.style.display = 'none';
            });
        """)
    except Exception:
        pass


def screenshot_product(page, url: str, title: str, out_dir: str):
    page.goto(url, wait_until="networkidle", timeout=60000)
    try:
        page.wait_for_selector("table.flt-table", timeout=15000)
    except Exception:
        pass
    _hide_popup(page)

    soup = BeautifulSoup(page.content(), "html.parser")
    tables = soup.find_all("table", class_="flt-table")

    if not tables:
        print(f"  [{title}] таблиц не найдено, пропускаем")
        return

    slug = slugify(title)

    for i, table in enumerate(tables, 1):
        clean_table(table)

        full_html = HTML_TEMPLATE.format(table_html=str(table))
        encoded = full_html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        page.evaluate(f"document.open(); document.write(`{encoded}`); document.close();")
        page.wait_for_load_state("domcontentloaded")

        dims = page.evaluate("""() => {
            var t = document.querySelector('table');
            if (!t) return {width: 1200, height: 600};
            var r = t.getBoundingClientRect();
            return {width: Math.ceil(r.width) + 32, height: Math.ceil(r.height) + 32};
        }""")

        w = max(dims["width"], 400)
        h = max(dims["height"], 100)
        page.set_viewport_size({"width": w, "height": h})

        out_path = os.path.join(out_dir, f"{slug}_table_{i}.png")
        page.screenshot(path=out_path, full_page=True)
        size_kb = Path(out_path).stat().st_size // 1024
        print(f"  таблица {i}/{len(tables)} -> {out_path} ({w}x{h}px, {size_kb} КБ)")


def main():
    missing = find_missing()
    print(f"Товаров без скринов: {len(missing)}")

    if not missing:
        print("Всё уже есть!")
        return

    for _, _, out_dir in missing:
        os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, (url, title, out_dir) in enumerate(missing, 1):
            print(f"\n[{i}/{len(missing)}] {title}")
            print(f"  {url}")
            try:
                screenshot_product(page, url, title, out_dir)
            except Exception as e:
                print(f"  ОШИБКА: {e}")

        browser.close()

    print("\nГотово.")


if __name__ == "__main__":
    main()
