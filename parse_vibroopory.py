"""
Парсер каталога виброопор с alterv.ru/catalog/vibroopory/
Эмулирует клики "Показать еще" до полной загрузки, затем парсит все товары.
"""

import csv
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CATALOG_URL = "https://alterv.ru/catalog/vibroopory/"
OUT_FILE = "alterv_vibroopory.csv"
FIXED_COLS = ["Категория", "URL товара", "Фото основные", "Фото дополнительные", "Применение HTML"]
BASE_URL = "https://alterv.ru"


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


def get_product_links(page):
    print(f"Загружаю каталог: {CATALOG_URL}")
    page.goto(CATALOG_URL, wait_until="networkidle", timeout=60000)
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
        print(f"  Страница пагинации: {pg_url}")
        page.goto(pg_url, wait_until="networkidle", timeout=60000)
        try:
            page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
        except Exception:
            pass
        _hide_popup(page)
        _click_show_more(page)
        _collect_links(page, seen, links)

    print(f"Найдено товаров: {len(links)}")
    return links


def get_prim_html(page) -> str:
    """Кликает таб 'Применение' и возвращает innerHTML блока #prim."""
    try:
        tab = page.query_selector("a[href='#prim']")
        if not tab:
            return ""
        page.evaluate("document.querySelector(\"a[href='#prim']\").click()")
        page.wait_for_selector("#prim.active, #prim.tab-pane_new", timeout=5000)
        html = page.evaluate("document.getElementById('prim') ? document.getElementById('prim').innerHTML : ''")
        return html.strip() if html else ""
    except Exception:
        return ""


def get_images(html: str) -> tuple[str, str]:
    """Возвращает (основные_через_запятую, дополнительные_через_запятую)."""
    soup = BeautifulSoup(html, "html.parser")
    main_imgs = []
    extra_imgs = []
    seen = set()
    for a in soup.select("a[data-fancybox-group]"):
        href = a.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)
        full = BASE_URL + href if href.startswith("/") else href
        group = a.get("data-fancybox-group", "")
        if group == "item_slider":
            main_imgs.append(full)
        elif group == "drawings":
            extra_imgs.append(full)
    return ", ".join(main_imgs), ", ".join(extra_imgs)


def get_table_headers(html: str) -> list:
    """Возвращает список заголовков со ВСЕХ таблиц flt-table на странице."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_="flt-table")
    headers = []
    seen = set()
    for table in tables:
        thead = table.find("thead")
        if not thead:
            continue
        for th in thead.find_all("th"):
            title_span = th.find("span", class_="flt-table__title")
            name = title_span.get_text(strip=True) if title_span else th.get_text(strip=True)
            if name and name != "Заказать" and name not in seen:
                seen.add(name)
                headers.append(name)
    return headers


def parse_product_rows(html: str, category: str, url: str, all_cols: list, prim_html: str = "") -> list:
    """Парсит строки всех таблиц flt-table, маппит по заголовкам в общий список колонок."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_="flt-table")
    if not tables:
        return []

    main_imgs, extra_imgs = get_images(html)
    rows = []

    for table in tables:
        thead = table.find("thead")
        local_cols = []
        if thead:
            for th in thead.find_all("th"):
                title_span = th.find("span", class_="flt-table__title")
                name = title_span.get_text(strip=True) if title_span else th.get_text(strip=True)
                local_cols.append(name)

        col_index = {name: i for i, name in enumerate(local_cols)}

        tbody = table.find("tbody")

        for tr in (tbody or table).find_all("tr", class_="table_row"):
            cells = tr.find_all("td")
            if not cells:
                continue

            def get_cell(idx):
                if idx < 0 or idx >= len(cells):
                    return ""
                td = cells[idx]

                nal_cell = td.find("span", class_="nal_cell")
                if nal_cell:
                    p1 = nal_cell.find("span", class_="p1")
                    if p1:
                        return p1.get_text(strip=True)
                    btn = nal_cell.find("button")
                    return btn.get_text(strip=True) if btn else nal_cell.get_text(strip=True)

                price_div = td.find("div", class_="table_price")
                if price_div:
                    price_val = price_div.get("price", "")
                    return price_val.replace(".", ",") if price_val else ""

                span = td.find("span")
                return span.get_text(strip=True) if span else td.get_text(strip=True)

            row = [category, url, main_imgs, extra_imgs, prim_html]
            for col_name in all_cols:
                idx = col_index.get(col_name, -1)
                row.append(get_cell(idx))

            rows.append(row)

    return rows


def main():
    page_cache = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        product_links = get_product_links(page)
        if not product_links:
            print("Товары не найдены!")
            browser.close()
            return

        # Проход 1: собираем все уникальные заголовки
        print("\n--- Проход 1: сбор заголовков ---")
        all_cols_ordered = []
        seen_cols = set()

        for i, (title, url) in enumerate(product_links, 1):
            print(f"[{i}/{len(product_links)}] {title}")
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                try:
                    page.wait_for_selector("tr.table_row", timeout=15000)
                except Exception:
                    pass
                html = page.content()
                prim_html = get_prim_html(page)
                page_cache[url] = (title, html, prim_html)

                for h in get_table_headers(html):
                    if h not in seen_cols:
                        seen_cols.add(h)
                        all_cols_ordered.append(h)
                        print(f"  + новая колонка: {h}")

            except Exception as e:
                print(f"  ОШИБКА: {e}")
                page_cache[url] = (title, "", "")

            time.sleep(0.3)

        print(f"\nВсего уникальных колонок: {len(all_cols_ordered)}")
        print(f"Колонки: {all_cols_ordered}")

        browser.close()

    # Проход 2: парсим строки из кэша
    print("\n--- Проход 2: парсинг данных ---")
    all_rows = []

    for url, (title, html, prim_html) in page_cache.items():
        if not html:
            continue
        rows = parse_product_rows(html, title, url, all_cols_ordered, prim_html=prim_html)
        print(f"  {title}: {len(rows)} строк")
        all_rows.extend(rows)

    print(f"\nВсего строк: {len(all_rows)}")

    final_headers = FIXED_COLS + all_cols_ordered
    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(final_headers)
        writer.writerows(all_rows)

    print(f"Сохранено в: {OUT_FILE}")
    print("Открывай в Excel — разделитель точка с запятой (;)")


if __name__ == "__main__":
    main()
