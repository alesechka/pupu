"""
Тест пагинации: проверяет что get_product_links каждого парсера
находит ожидаемое количество товаров.

Эталонные значения из предыдущих успешных запусков:
  vibroizolyatory  — 12
  vibroopory       — 22
  dempfery         —  8
  rukoyatki        —  3
  rychagi          — 39
  zamki            — 94
"""

import sys
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://alterv.ru"

CATALOGS = [
    ("vibroizolyatory", "https://alterv.ru/catalog/vibroizolyatory/", 12),
    ("vibroopory",      "https://alterv.ru/catalog/vibroopory/",      22),
    ("dempfery",        "https://alterv.ru/catalog/dempfery/",         8),
    ("rukoyatki",       "https://alterv.ru/catalog/rukoyatki_zazhimnye/", 3),
    ("rychagi",         "https://alterv.ru/catalog/rychagi_zazhimnye/", 39),
    ("zamki",           "https://alterv.ru/catalog/zamki_povorotnye/", 94),
]


# ---------- общие хелперы (копия из парсеров) ----------

def _hide_popup(page):
    try:
        page.evaluate("""
            ['altasib_geobase_window','altasib_geobase_window_block'].forEach(id => {
                var el = document.getElementById(id); if (el) el.style.display = 'none';
            });
        """)
    except Exception:
        pass


def _click_show_more(page):
    while True:
        prev = len(page.query_selector_all(".catalog_item_wrapp"))
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
        for _ in range(30):
            time.sleep(0.5)
            if len(page.query_selector_all(".catalog_item_wrapp")) > prev:
                break
        _hide_popup(page)


def _get_pagination_urls(page) -> list:
    soup = BeautifulSoup(page.content(), "html.parser")
    seen, urls = set(), []
    for a in soup.select(".module-pagination .nums a.dark_link"):
        href = a.get("href", "")
        if href and href not in seen:
            seen.add(href)
            urls.append(BASE_URL + href if href.startswith("/") else href)
    return urls


def _collect_links(page, seen: set, links: list):
    soup = BeautifulSoup(page.content(), "html.parser")
    for item in soup.select(".catalog_item_wrapp .item-title a"):
        href = item.get("href", "")
        if href and href not in seen:
            seen.add(href)
            full_url = BASE_URL + href if href.startswith("/") else href
            links.append((item.get_text(strip=True), full_url))


def get_product_links(page, catalog_url: str) -> list:
    page.goto(catalog_url, wait_until="networkidle", timeout=60000)
    try:
        page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
    except Exception:
        pass
    _hide_popup(page)

    links, seen = [], set()
    _click_show_more(page)
    pagination_urls = _get_pagination_urls(page)
    _collect_links(page, seen, links)

    for pg_url in pagination_urls:
        page.goto(pg_url, wait_until="networkidle", timeout=60000)
        try:
            page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
        except Exception:
            pass
        _hide_popup(page)
        _click_show_more(page)
        _collect_links(page, seen, links)

    return links


# ---------- тест ----------

def run_tests():
    results = []
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for name, url, expected in CATALOGS:
            print(f"\n[{name}] ожидается: {expected} товаров")
            try:
                links = get_product_links(page, url)
                got = len(links)
                ok = got == expected
                status = "OK" if ok else "FAIL"
                if not ok:
                    failed += 1
                print(f"  -> {status}: найдено {got}")
                results.append((name, expected, got, ok))
            except Exception as e:
                print(f"  -> ERROR: {e}")
                results.append((name, expected, "ERROR", False))
                failed += 1

        browser.close()

    # итог
    print("\n" + "=" * 50)
    print(f"{'Каталог':<20} {'Ожидалось':>10} {'Найдено':>10} {'Статус':>8}")
    print("-" * 50)
    for name, exp, got, ok in results:
        status = "OK" if ok else "FAIL"
        print(f"{name:<20} {exp:>10} {str(got):>10} {status:>8}")
    print("=" * 50)
    print(f"Итог: {len(results) - failed}/{len(results)} тестов прошло")

    return failed


if __name__ == "__main__":
    failed = run_tests()
    sys.exit(1 if failed else 0)
