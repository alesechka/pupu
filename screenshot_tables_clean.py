"""
Делает PNG-скриншоты таблиц flt-table со страниц товаров.
Отличия от screenshot_tables.py:
  - Удаляет строку "Сбросить фильтр" (tfoot / любая tr с таким текстом)
  - Обрезает колонки начиная с "Наличие" и правее (включая Наличие)
  - Удаляет "В избранное" и иконку сердечка из ячеек
Результат в папке table_screenshots_clean/
"""

import os
import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://alterv.ru"
OUT_DIR = "table_screenshots_no_favorites"

CATALOGS = [
    "https://alterv.ru/catalog/vibroizolyatory/",
    "https://alterv.ru/catalog/vibroopory/",
    "https://alterv.ru/catalog/dempfery/",
    "https://alterv.ru/catalog/rukoyatki_zazhimnye/",
    "https://alterv.ru/catalog/rychagi_zazhimnye/",
    "https://alterv.ru/catalog/zamki_povorotnye/",
]

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

# Колонки начиная с которой (включительно) всё обрезается
CUT_FROM_COLS = {"наличие", "наличие, шт"}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text)
    return text[:60]


def get_col_text(th) -> str:
    """Извлекает текст заголовка колонки в нижнем регистре."""
    span = th.find("span", class_="flt-table__title")
    raw = span.get_text(strip=True) if span else th.get_text(strip=True)
    return raw.lower()


def clean_table(table) -> None:
    """
    Мутирует объект BeautifulSoup table:
    1. Удаляет tfoot и любые tr содержащие только "Сбросить фильтр"
    2. Определяет индекс колонки "Наличие" и удаляет её и все правее
    """
    # --- 1. Убираем "Сбросить фильтр" ---
    for tfoot in table.find_all("tfoot"):
        tfoot.decompose()

    for tr in table.find_all("tr"):
        text = tr.get_text(strip=True).lower()
        if "сбросить фильтр" in text:
            tr.decompose()

    # --- 2. Убираем "В избранное" и иконку сердечка ---
    # Удаляем любые теги с классами связанными с избранным
    for el in table.select(".favorites, .fav, .in-favorites, .add-to-favorites, "
                           "[class*='favorit'], [class*='wishlist'], [class*='heart']"):
        el.decompose()
    # Удаляем ссылки/кнопки содержащие текст "в избранное"
    for el in table.find_all(["a", "button", "span", "div"]):
        if "в избранное" in el.get_text(strip=True).lower():
            el.decompose()

    # --- 2. Находим индекс колонки "Наличие" ---
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
        return  # колонки "Наличие" нет — ничего не режем

    # Удаляем th начиная с cut_index
    for th in headers[cut_index:]:
        th.decompose()

    # Удаляем td в каждой строке tbody начиная с cut_index
    tbody = table.find("tbody")
    if not tbody:
        return

    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        for td in cells[cut_index:]:
            td.decompose()


def get_product_links(page, catalog_url: str) -> list[tuple[str, str]]:
    print(f"\nКаталог: {catalog_url}")
    page.goto(catalog_url, wait_until="networkidle", timeout=60000)

    page.evaluate("""
        ['altasib_geobase_window','altasib_geobase_window_block'].forEach(id => {
            var el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    """)

    while True:
        btn = page.query_selector(".ajax_load_btn")
        if not btn or not btn.is_visible():
            break
        page.evaluate("document.querySelector('.ajax_load_btn').click()")
        time.sleep(2)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.evaluate("""
            var el = document.getElementById('altasib_geobase_window');
            if (el) el.style.display = 'none';
        """)

    soup = BeautifulSoup(page.content(), "html.parser")
    links = []
    seen = set()
    for a in soup.select(".catalog_item_wrapp .item-title a"):
        href = a.get("href", "")
        if href and href not in seen:
            seen.add(href)
            full_url = BASE_URL + href if href.startswith("/") else href
            links.append((a.get_text(strip=True), full_url))

    print(f"  Найдено товаров: {len(links)}")
    return links


def screenshot_tables(page, title: str, url: str, out_dir: str):
    page.goto(url, wait_until="networkidle", timeout=60000)
    try:
        page.wait_for_selector("table.flt-table", timeout=15000)
    except Exception:
        pass

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_="flt-table")

    if not tables:
        print(f"  [{title}] таблиц не найдено, пропускаем")
        return

    slug = slugify(title)

    for i, table in enumerate(tables, 1):
        clean_table(table)  # убираем "Сбросить фильтр" и лишние колонки

        table_html = str(table)
        full_html = HTML_TEMPLATE.format(table_html=table_html)

        encoded = full_html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        page.evaluate(f"""
            document.open();
            document.write(`{encoded}`);
            document.close();
        """)
        page.wait_for_load_state("domcontentloaded")

        dims = page.evaluate("""() => {
            var t = document.querySelector('table');
            if (!t) return {width: 1200, height: 600};
            var r = t.getBoundingClientRect();
            return {width: Math.ceil(r.width) + 32, height: Math.ceil(r.height) + 32};
        }""")

        width = max(dims["width"], 400)
        height = max(dims["height"], 100)
        page.set_viewport_size({"width": width, "height": height})

        out_path = os.path.join(out_dir, f"{slug}_table_{i}.png")
        page.screenshot(path=out_path, full_page=True)
        print(f"  [{title}] таблица {i}/{len(tables)} -> {out_path} ({width}x{height}px)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for catalog_url in CATALOGS:
            links = get_product_links(page, catalog_url)
            for title, url in links:
                try:
                    screenshot_tables(page, title, url, OUT_DIR)
                except Exception as e:
                    print(f"  ОШИБКА [{title}]: {e}")

        browser.close()

    print(f"\nГотово. Скриншоты в папке: {OUT_DIR}/")


if __name__ == "__main__":
    main()
