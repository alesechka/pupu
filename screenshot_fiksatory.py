"""
Скриншоты таблиц flt-table для каталога фиксаторов поворотных.
Clean вариант: убирает "Сбросить фильтр", обрезает от "Наличие", убирает "В избранное".
Результат в папке table_screenshots_fiksatory/
"""

import os
import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://alterv.ru"
CATALOG_URL = "https://alterv.ru/catalog/fiksatory_povorotnye/"
OUT_DIR = "table_screenshots_fiksatory"

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


def get_col_text(th) -> str:
    span = th.find("span", class_="flt-table__title")
    raw = span.get_text(strip=True) if span else th.get_text(strip=True)
    return raw.lower()


def clean_table(table):
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
        for td in tr.find_all("td")[cut_index:]:
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


def _click_show_more(page) -> int:
    click_count = 0
    while True:
        prev_count = len(page.query_selector_all(".catalog_item_wrapp"))
        btn = page.query_selector(".ajax_load_btn")
        if not btn or not btn.is_visible():
            appeared = False
            for _ in range(10):
                time.sleep(0.5)
                btn = page.query_selector(".ajax_load_btn")
                if btn and btn.is_visible():
                    appeared = True
                    break
            if not appeared:
                break
        page.evaluate("document.querySelector('.ajax_load_btn').click()")
        click_count += 1
        for _ in range(30):
            time.sleep(0.5)
            if len(page.query_selector_all(".catalog_item_wrapp")) > prev_count:
                break
        _hide_popup(page)
    return click_count


def _collect_links(page, seen: set, links: list):
    soup = BeautifulSoup(page.content(), "html.parser")
    for a in soup.select(".catalog_item_wrapp .item-title a"):
        href = a.get("href", "")
        if href and href not in seen:
            seen.add(href)
            full_url = BASE_URL + href if href.startswith("/") else href
            links.append((a.get_text(strip=True), full_url))


def _get_pagination_urls(page) -> list:
    soup = BeautifulSoup(page.content(), "html.parser")
    urls, seen = [], set()
    for a in soup.select(".module-pagination .nums a.dark_link"):
        href = a.get("href", "")
        if href and href not in seen:
            seen.add(href)
            urls.append(BASE_URL + href if href.startswith("/") else href)
    return urls


def get_product_links(page) -> list:
    print(f"Загружаю каталог: {CATALOG_URL}")
    page.goto(CATALOG_URL, wait_until="networkidle", timeout=60000)
    try:
        page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
    except Exception:
        pass
    _hide_popup(page)

    links, seen = [], set()
    clicks = _click_show_more(page)
    print(f"  Стр.1: кликов={clicks}, товаров={len(page.query_selector_all('.catalog_item_wrapp'))}")
    pagination_urls = _get_pagination_urls(page)
    _collect_links(page, seen, links)

    for pg_url in pagination_urls:
        print(f"  Страница пагинации: {pg_url}")
        page.goto(pg_url, wait_until="networkidle", timeout=60000)
        try:
            page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
        except Exception:
            pass
        _hide_popup(page)
        clicks = _click_show_more(page)
        print(f"    кликов={clicks}, товаров={len(page.query_selector_all('.catalog_item_wrapp'))}")
        _collect_links(page, seen, links)

    print(f"Найдено товаров всего: {len(links)}")
    return links


def screenshot_tables(page, title: str, url: str):
    page.goto(url, wait_until="networkidle", timeout=60000)
    try:
        page.wait_for_selector("table.flt-table", timeout=15000)
    except Exception:
        pass

    soup = BeautifulSoup(page.content(), "html.parser")
    tables = soup.find_all("table", class_="flt-table")
    if not tables:
        print(f"  [{title}] таблиц не найдено")
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

        out_path = os.path.join(OUT_DIR, f"{slug}_table_{i}.png")
        page.screenshot(path=out_path, full_page=True)
        size_kb = os.path.getsize(out_path) // 1024
        print(f"  [{title}] таблица {i}/{len(tables)} -> {slug}_table_{i}.png ({w}x{h}px, {size_kb} КБ)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        links = get_product_links(page)
        for title, url in links:
            try:
                screenshot_tables(page, title, url)
            except Exception as e:
                print(f"  ОШИБКА [{title}]: {e}")

        browser.close()

    print(f"\nГотово. Скриншоты в папке: {OUT_DIR}/")


if __name__ == "__main__":
    main()
