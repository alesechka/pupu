"""Парсит недостающие товары из opory и добавляет в alterv_opory.csv"""

import csv, time, re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pathlib import Path

MISSING_URLS = [
    "https://alterv.ru/catalog/plastiny_antiskolzheniya_dlya_opor/a00019_plastiny_antiskolzheniya_dlya_sharnirnykh_opor_20/",
    "https://alterv.ru/catalog/plastiny_antiskolzheniya_dlya_opor/pam_plastiny_antiskolzheniya_dlya_sharnirnykh_opor/",
    "https://alterv.ru/catalog/osnovaniya_dlya_opor/k0419_osnovaniya_sharnirnykh_opor_vibroizoliruyushchie_20/",
    "https://alterv.ru/catalog/opory_s_podvizhnym_vintom/k0420_opory_sharnirnye_vibroizoliruyushchie_15/",
    "https://alterv.ru/catalog/osnovaniya_dlya_opor/k0670_osnovaniya_opor_diskovye_vibroizoliruyushchie/",
    "https://alterv.ru/catalog/prostavki_raspornye/k0057_prostavki_raspornye_podvizhnye_na_4/",
]

BASE_URL = "https://alterv.ru"
CSV_FILE = "alterv_opory.csv"

TRANSLIT = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z',
    'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
    'с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh',
    'щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    'А':'a','Б':'b','В':'v','Г':'g','Д':'d','Е':'e','Ё':'yo','Ж':'zh','З':'z',
    'И':'i','Й':'y','К':'k','Л':'l','М':'m','Н':'n','О':'o','П':'p','Р':'r',
    'С':'s','Т':'t','У':'u','Ф':'f','Х':'kh','Ц':'ts','Ч':'ch','Ш':'sh',
    'Щ':'shch','Ъ':'','Ы':'y','Ь':'','Э':'e','Ю':'yu','Я':'ya',
}

def _hide_popup(page):
    try: page.evaluate("['altasib_geobase_window','altasib_geobase_window_block'].forEach(id=>{var el=document.getElementById(id);if(el)el.style.display='none';});")
    except: pass

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
    # Читаем существующий CSV
    p = Path(CSV_FILE)
    with open(p, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        headers = next(reader)
        existing_rows = list(reader)

    print(f"Существующих строк: {len(existing_rows)}")
    print(f"Колонок: {len(headers)}")

    # Определяем индексы
    cat_idx = headers.index("Категория")
    url_idx = headers.index("URL товара")
    fixed_count = 7  # FIXED_COLS count
    all_cols = headers[fixed_count:]

    page_cache = {}
    with sync_playwright() as p_pw:
        browser = p_pw.chromium.launch(headless=True)
        page = browser.new_page()

        for url in MISSING_URLS:
            print(f"\nПарсю: {url}")
            try:
                page.goto(url, wait_until="commit", timeout=60000)
                try: page.wait_for_selector("tr.table_row", timeout=15000)
                except: pass
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")
                # Получаем название товара
                title_el = soup.select_one("h1")
                title = title_el.get_text(strip=True) if title_el else url.split("/")[-2]
                prim_html = get_prim_html(page)
                breadcrumb = get_breadcrumbs(html)
                brand = get_brand(html)
                page_cache[url] = (title, html, prim_html, breadcrumb, brand)
                print(f"  Название: {title}")
                print(f"  Бренд: {brand}")
                new_headers = get_table_headers(html)
                for h in new_headers:
                    if h not in all_cols:
                        print(f"  НОВАЯ КОЛОНКА: {h} — добавляем")
                        all_cols.append(h)
                        headers.append(h)
                        for row in existing_rows:
                            while len(row) < len(headers):
                                row.append("")
            except Exception as e:
                print(f"  ОШИБКА: {e}")
            time.sleep(0.3)

        browser.close()

    # Парсим строки
    new_rows = []
    for url, (title, html, prim_html, breadcrumb, brand) in page_cache.items():
        rows = parse_product_rows(html, title, url, breadcrumb, all_cols, prim_html=prim_html, brand=brand)
        print(f"  {title}: {len(rows)} строк")
        new_rows.extend(rows)

    print(f"\nНовых строк: {len(new_rows)}")

    # Записываем обратно
    all_rows = existing_rows + new_rows
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(all_rows)

    print(f"Итого строк: {len(all_rows)}")
    print("Готово.")

if __name__ == "__main__":
    main()
