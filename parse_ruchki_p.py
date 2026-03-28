"""Парсер каталога ручек П-образных. https://alterv.ru/catalog/ruchki_p_obraznye/"""

import csv, time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CATALOG_URL = "https://alterv.ru/catalog/ruchki_p_obraznye/"
OUT_FILE = "alterv_ruchki_p.csv"
FIXED_COLS = ["Категория", "URL товара", "Бренд", "Путь", "Фото основные", "Фото дополнительные", "Применение HTML"]
BASE_URL = "https://alterv.ru"

def _hide_popup(page):
    try:
        page.evaluate("['altasib_geobase_window','altasib_geobase_window_block'].forEach(id=>{var el=document.getElementById(id);if(el)el.style.display='none';});")
    except: pass

def _click_show_more(page):
    while True:
        prev = len(page.query_selector_all(".catalog_item_wrapp"))
        btn = page.query_selector(".ajax_load_btn")
        if not btn or not btn.is_visible():
            appeared = False
            for _ in range(10):
                time.sleep(0.5)
                btn = page.query_selector(".ajax_load_btn")
                if btn and btn.is_visible(): appeared = True; break
            if not appeared: break
        page.evaluate("document.querySelector('.ajax_load_btn').click()")
        for _ in range(30):
            time.sleep(0.5)
            if len(page.query_selector_all(".catalog_item_wrapp")) > prev: break
        _hide_popup(page)

def _get_pagination_urls(page):
    soup = BeautifulSoup(page.content(), "html.parser")
    seen, urls = set(), []
    # Пробуем разные селекторы пагинации
    for a in soup.select(".module-pagination a, .nums a, [class*='pagination'] a"):
        href = a.get("href", "")
        if href and "PAGEN" in href and href not in seen:
            seen.add(href)
            urls.append(BASE_URL + href if href.startswith("/") else href)
    return urls

def _collect_links(page, seen, links):
    soup = BeautifulSoup(page.content(), "html.parser")
    for item in soup.select(".catalog_item_wrapp .item-title a"):
        href = item.get("href", "")
        if href and href not in seen:
            seen.add(href)
            links.append((item.get_text(strip=True), BASE_URL + href if href.startswith("/") else href))

def get_product_links(page):
    print(f"Загружаю: {CATALOG_URL}")
    page.goto(CATALOG_URL, wait_until="networkidle", timeout=60000)
    try: page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
    except: pass
    _hide_popup(page)
    links, seen = [], set()
    _click_show_more(page)
    print(f"  Стр.1: {len(page.query_selector_all('.catalog_item_wrapp'))}")
    _collect_links(page, seen, links)
    # Перебираем страницы последовательно
    page_num = 2
    while True:
        pg_url = f"{CATALOG_URL}?PAGEN_2={page_num}"
        page.goto(pg_url, wait_until="networkidle", timeout=60000)
        try: page.wait_for_selector(".catalog_item_wrapp", timeout=10000)
        except: break
        _hide_popup(page); _click_show_more(page)
        prev_count = len(links)
        _collect_links(page, seen, links)
        print(f"  Стр.{page_num}: товаров={len(page.query_selector_all('.catalog_item_wrapp'))}, новых={len(links)-prev_count}")
        if len(links) == prev_count:
            break
        page_num += 1
    print(f"Найдено: {len(links)}")
    return links

def get_brand(html):
    soup = BeautifulSoup(html, "html.parser")
    p = soup.find("p", class_="manufacturer")
    if not p: return ""
    a = p.find("a")
    return a.get_text(strip=True) if a else ""

def get_breadcrumbs(html):
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.find("div", id="navigation")
    if not nav: return ""
    parts = []
    for item in nav.find_all("div", class_="bx-breadcrumb-item"):
        span = item.find("span", itemprop="name")
        if span:
            t = span.get_text(strip=True)
            if t: parts.append(t)
    for s in nav.find_all("span", recursive=False):
        if "separator" not in s.get("class", []):
            t = s.get_text(strip=True)
            if t: parts.append(t)
    return " > ".join(parts)

def get_prim_html(page):
    try:
        tab = page.query_selector("a[href='#prim']")
        if not tab: return ""
        page.evaluate("document.querySelector(\"a[href='#prim']\").click()")
        page.wait_for_selector("#prim.active, #prim.tab-pane_new", timeout=5000)
        html = page.evaluate("document.getElementById('prim')?document.getElementById('prim').innerHTML:''")
        return html.strip() if html else ""
    except: return ""

def get_images(html):
    soup = BeautifulSoup(html, "html.parser")
    main_imgs, extra_imgs, seen = [], [], set()
    for a in soup.select("a[data-fancybox-group]"):
        href = a.get("href", "")
        if not href or href in seen: continue
        seen.add(href)
        full = BASE_URL + href if href.startswith("/") else href
        g = a.get("data-fancybox-group", "")
        if g == "item_slider": main_imgs.append(full)
        elif g == "drawings": extra_imgs.append(full)
    return ", ".join(main_imgs), ", ".join(extra_imgs)

def get_table_headers(html):
    soup = BeautifulSoup(html, "html.parser")
    headers, seen = [], set()
    for table in soup.find_all("table", class_="flt-table"):
        thead = table.find("thead")
        if not thead: continue
        for th in thead.find_all("th"):
            span = th.find("span", class_="flt-table__title")
            name = span.get_text(strip=True) if span else th.get_text(strip=True)
            if name and name != "Заказать" and name not in seen:
                seen.add(name); headers.append(name)
    return headers

def parse_product_rows(html, category, url, breadcrumb, all_cols, prim_html="", brand=""):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_="flt-table")
    if not tables: return []
    main_imgs, extra_imgs = get_images(html)
    rows = []
    for table in tables:
        thead = table.find("thead")
        local_cols = []
        if thead:
            for th in thead.find_all("th"):
                span = th.find("span", class_="flt-table__title")
                local_cols.append(span.get_text(strip=True) if span else th.get_text(strip=True))
        col_index = {n: i for i, n in enumerate(local_cols)}
        tbody = table.find("tbody")
        for tr in (tbody or table).find_all("tr", class_="table_row"):
            cells = tr.find_all("td")
            if not cells: continue
            def get_cell(idx):
                if idx < 0 or idx >= len(cells): return ""
                td = cells[idx]
                nal = td.find("span", class_="nal_cell")
                if nal:
                    p1 = nal.find("span", class_="p1")
                    if p1: return p1.get_text(strip=True)
                    btn = nal.find("button")
                    return btn.get_text(strip=True) if btn else nal.get_text(strip=True)
                price = td.find("div", class_="table_price")
                if price:
                    v = price.get("price", "")
                    return v.replace(".", ",") if v else ""
                span = td.find("span")
                return span.get_text(strip=True) if span else td.get_text(strip=True)
            row = [category, url, brand, breadcrumb, main_imgs, extra_imgs, prim_html]
            for col_name in all_cols:
                row.append(get_cell(col_index.get(col_name, -1)))
            rows.append(row)
    return rows

def main():
    page_cache = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        product_links = get_product_links(page)
        if not product_links:
            print("Товары не найдены!"); browser.close(); return
        print(f"\n--- Проход 1: сбор заголовков ---")
        all_cols_ordered, seen_cols = [], set()
        for i, (title, url) in enumerate(product_links, 1):
            print(f"[{i}/{len(product_links)}] {title}")
            try:
                page.goto(url, wait_until="commit", timeout=60000)
                try: page.wait_for_selector("tr.table_row", timeout=15000)
                except: pass
                html = page.content()
                prim_html = get_prim_html(page)
                breadcrumb = get_breadcrumbs(html)
                brand = get_brand(html)
                page_cache[url] = (title, html, prim_html, breadcrumb, brand)
                print(f"  Бренд: {brand} | Путь: {breadcrumb[:60]}")
                for h in get_table_headers(html):
                    if h not in seen_cols:
                        seen_cols.add(h); all_cols_ordered.append(h); print(f"  + {h}")
            except Exception as e:
                print(f"  ОШИБКА: {e}"); page_cache[url] = (title, "", "", "", "")
            time.sleep(0.3)
        print(f"\nКолонок: {len(all_cols_ordered)}")
        browser.close()
    print("\n--- Проход 2: парсинг ---")
    all_rows = []
    for url, (title, html, prim_html, breadcrumb, brand) in page_cache.items():
        if not html: continue
        rows = parse_product_rows(html, title, url, breadcrumb, all_cols_ordered, prim_html=prim_html, brand=brand)
        print(f"  {title}: {len(rows)} строк")
        all_rows.extend(rows)
    print(f"\nВсего строк: {len(all_rows)}")
    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(FIXED_COLS + all_cols_ordered)
        writer.writerows(all_rows)
    print(f"Сохранено в: {OUT_FILE}")

if __name__ == "__main__":
    main()
