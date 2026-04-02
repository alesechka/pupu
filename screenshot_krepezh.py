"""Скриншоты: https://alterv.ru/catalog/krepezhnye_elementy/ — имена файлов только латиница"""

import os, re, time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://alterv.ru"
CATALOG_URL = "https://alterv.ru/catalog/krepezhnye_elementy/"
OUT_DIR = "table_screenshots_krepezh"
CUT_FROM_COLS = {"наличие", "наличие, шт"}

HTML_TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:16px;background:#fff;font-family:Arial,sans-serif;font-size:13px;}}
table{{border-collapse:collapse;white-space:nowrap;}}
th,td{{border:1px solid #ccc;padding:6px 10px;text-align:left;}}
thead th{{background:#f0f0f0;font-weight:bold;}}
tr:nth-child(even){{background:#fafafa;}}
</style></head><body>{table_html}</body></html>"""

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

def transliterate(text):
    return ''.join(TRANSLIT.get(c, c) for c in text)

def slugify(text):
    text = transliterate(text.strip().lower())
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text)
    return text[:60]

def clean_table(table):
    for tfoot in table.find_all("tfoot"): tfoot.decompose()
    for tr in table.find_all("tr"):
        if "сбросить фильтр" in tr.get_text(strip=True).lower(): tr.decompose()
    for el in table.find_all(["a","button","span","div"]):
        if "в избранное" in el.get_text(strip=True).lower(): el.decompose()
    thead = table.find("thead")
    if not thead: return
    headers = thead.find_all("th")
    cut_index = None
    for i, th in enumerate(headers):
        span = th.find("span", class_="flt-table__title")
        col = (span.get_text(strip=True) if span else th.get_text(strip=True)).lower()
        if col in CUT_FROM_COLS: cut_index = i; break
    if cut_index is None: return
    for th in headers[cut_index:]: th.decompose()
    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            for td in tr.find_all("td")[cut_index:]: td.decompose()

def _hide_popup(page):
    try: page.evaluate("['altasib_geobase_window','altasib_geobase_window_block'].forEach(id=>{var el=document.getElementById(id);if(el)el.style.display='none';});")
    except: pass

def _click_show_more(page):
    while True:
        prev = len(page.query_selector_all(".catalog_item_wrapp"))
        btn = page.query_selector(".ajax_load_btn")
        if not btn or not btn.is_visible():
            appeared = False
            for _ in range(10):
                time.sleep(0.5); btn = page.query_selector(".ajax_load_btn")
                if btn and btn.is_visible(): appeared = True; break
            if not appeared: break
        page.evaluate("document.querySelector('.ajax_load_btn').click()")
        for _ in range(30):
            time.sleep(0.5)
            if len(page.query_selector_all(".catalog_item_wrapp")) > prev: break
        _hide_popup(page)

def _collect_links(page, seen, links):
    soup = BeautifulSoup(page.content(), "html.parser")
    for a in soup.select(".catalog_item_wrapp .item-title a"):
        href = a.get("href", "")
        if href and href not in seen:
            seen.add(href)
            links.append((a.get_text(strip=True), BASE_URL + href if href.startswith("/") else href))

def get_product_links(page):
    print(f"Загружаю: {CATALOG_URL}")
    page.goto(CATALOG_URL, wait_until="networkidle", timeout=60000)
    try: page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
    except: pass
    _hide_popup(page)
    links, seen = [], set()
    _click_show_more(page)
    _collect_links(page, seen, links)
    page_num = 2
    while True:
        pg_url = f"{CATALOG_URL}?PAGEN_2={page_num}"
        page.goto(pg_url, wait_until="networkidle", timeout=60000)
        try: page.wait_for_selector(".catalog_item_wrapp", timeout=10000)
        except: break
        _hide_popup(page); _click_show_more(page)
        prev_count = len(links)
        _collect_links(page, seen, links)
        print(f"  Стр.{page_num}: новых={len(links)-prev_count}")
        if len(links) == prev_count: break
        page_num += 1
    print(f"Товаров: {len(links)}")
    return links

def screenshot_tables(page, title, url):
    page.goto(url, wait_until="networkidle", timeout=60000)
    try: page.wait_for_selector("table.flt-table", timeout=15000)
    except: pass
    soup = BeautifulSoup(page.content(), "html.parser")
    tables = soup.find_all("table", class_="flt-table")
    if not tables: print(f"  [{title}] таблиц не найдено"); return
    slug = slugify(title)
    for i, table in enumerate(tables, 1):
        clean_table(table)
        full_html = HTML_TEMPLATE.format(table_html=str(table))
        encoded = full_html.replace("\\","\\\\").replace("`","\\`").replace("${","\\${")
        page.evaluate(f"document.open();document.write(`{encoded}`);document.close();")
        page.wait_for_load_state("domcontentloaded")
        dims = page.evaluate("()=>{var t=document.querySelector('table');if(!t)return{width:1200,height:600};var r=t.getBoundingClientRect();return{width:Math.ceil(r.width)+32,height:Math.ceil(r.height)+32};}")
        w, h = max(dims["width"], 400), max(dims["height"], 100)
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
            try: screenshot_tables(page, title, url)
            except Exception as e: print(f"  ОШИБКА [{title}]: {e}")
        browser.close()
    print(f"\nГотово. Скриншоты в: {OUT_DIR}/")

if __name__ == "__main__":
    main()
