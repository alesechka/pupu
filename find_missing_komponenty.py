"""Находит товары на сайте, которых нет в alterv_komponenty.csv"""
import csv, time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CATALOG_URL = "https://alterv.ru/catalog/komponenty_dlya_konstruktsionnogo_profilya/"
BASE_URL = "https://alterv.ru"
CSV_FILE = "alterv_komponenty.csv"

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
    for item in soup.select(".catalog_item_wrapp .item-title a"):
        href = item.get("href", "")
        if href and href not in seen:
            seen.add(href)
            links.append((item.get_text(strip=True), BASE_URL + href if href.startswith("/") else href))

def get_site_links(page):
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
        if len(links) == prev_count: break
        page_num += 1
    return links

def get_csv_urls():
    urls = set()
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for row in reader:
            if len(row) > 1 and row[1]:
                urls.add(row[1].strip())
    return urls

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    site_links = get_site_links(page)
    browser.close()

csv_urls = get_csv_urls()
print(f"На сайте: {len(site_links)}")
print(f"В CSV: {len(csv_urls)}")

missing = [(t, u) for t, u in site_links if u not in csv_urls]
print(f"\nНедостающих: {len(missing)}")
for t, u in missing:
    print(f"  {t} | {u}")
