"""
Делает PNG-скриншоты таблиц flt-table со страниц товаров.
Каждая таблица — отдельный файл в папке table_screenshots/.
Имя файла: <артикул>_table_<N>.png
"""

import os
import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://alterv.ru"
OUT_DIR = "table_screenshots"

# Список каталогов для обхода
CATALOGS = [
    "https://alterv.ru/catalog/vibroizolyatory/",
    "https://alterv.ru/catalog/vibroopory/",
    "https://alterv.ru/catalog/dempfery/",
    "https://alterv.ru/catalog/rukoyatki_zazhimnye/",
    "https://alterv.ru/catalog/rychagi_zazhimnye/",
]

# HTML-обёртка для рендера таблицы
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


def get_product_links(page, catalog_url: str) -> list[tuple[str, str]]:
    print(f"\nКаталог: {catalog_url}")
    page.goto(catalog_url, wait_until="networkidle", timeout=60000)

    # Скрываем попап геолокации
    page.evaluate("""
        ['altasib_geobase_window','altasib_geobase_window_block'].forEach(id => {
            var el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    """)

    # Кликаем "Показать еще" пока есть
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
        table_html = str(table)
        full_html = HTML_TEMPLATE.format(table_html=table_html)

        # Открываем HTML в новой вкладке через data URL
        encoded = full_html.replace("`", "\\`")
        page.evaluate(f"""
            document.open();
            document.write(`{encoded}`);
            document.close();
        """)
        page.wait_for_load_state("domcontentloaded")

        # Получаем реальный размер таблицы
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
