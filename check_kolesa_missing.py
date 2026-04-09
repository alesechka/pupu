import csv, time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

existing_urls = set()
with open("alterv_kolesa.csv", encoding="utf-8-sig") as f:
    reader = csv.reader(f, delimiter=";")
    headers = next(reader)
    url_idx = headers.index("URL товара")
    for row in reader:
        if url_idx < len(row): existing_urls.add(row[url_idx])

print(f"Существующих URL: {len(existing_urls)}")

BASE_URL = "https://alterv.ru"
CATALOG_URL = "https://alterv.ru/catalog/kolesa_roliki_i_kolesnye_opory/"

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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    site_links = {}
    page_num = 1
    while True:
        pg_url = CATALOG_URL if page_num == 1 else f"{CATALOG_URL}?PAGEN_2={page_num}"
        page.goto(pg_url, wait_until="networkidle", timeout=60000)
        try: page.wait_for_selector(".catalog_item_wrapp", timeout=10000)
        except: break
        _hide_popup(page); _click_show_more(page)
        soup = BeautifulSoup(page.content(), "html.parser")
        items = soup.select(".catalog_item_wrapp .item-title a")
        if not items: break
        prev_count = len(site_links)
        for item in items:
            href = item.get("href", "")
            if href:
                full_url = BASE_URL + href if href.startswith("/") else href
                site_links[full_url] = item.get_text(strip=True)
        print(f"  Стр.{page_num}: {len(items)}, всего={len(site_links)}")
        if len(site_links) == prev_count: break
        page_num += 1
    browser.close()

print(f"\nВсего на сайте: {len(site_links)}")
missing = {url: title for url, title in site_links.items() if url not in existing_urls}
print(f"Отсутствует: {len(missing)}")
for url, title in missing.items():
    print(f"  {title}\n  {url}")
