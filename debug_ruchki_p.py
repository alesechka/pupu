"""Дебаг пагинации ruchki_p_obraznye"""
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CATALOG_URL = "https://alterv.ru/catalog/ruchki_p_obraznye/"
BASE_URL = "https://alterv.ru"

def _hide_popup(page):
    try: page.evaluate("['altasib_geobase_window','altasib_geobase_window_block'].forEach(id=>{var el=document.getElementById(id);if(el)el.style.display='none';});")
    except: pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(CATALOG_URL, wait_until="networkidle", timeout=60000)
    try: page.wait_for_selector(".catalog_item_wrapp", timeout=15000)
    except: pass
    _hide_popup(page)

    soup = BeautifulSoup(page.content(), "html.parser")
    items = soup.select(".catalog_item_wrapp .item-title a")
    print(f"Товаров на стр.1: {len(items)}")
    for item in items[:5]:
        print(f"  {item.get_text(strip=True)} -> {item.get('href','')}")

    # Все ссылки пагинации
    print("\nВсе ссылки пагинации:")
    for a in soup.select(".module-pagination a"):
        print(f"  {a.get_text(strip=True)} -> {a.get('href','')}")

    # Кнопка "показать ещё"
    btn = page.query_selector(".ajax_load_btn")
    print(f"\nКнопка 'показать ещё': {'есть' if btn and btn.is_visible() else 'нет'}")

    # Общее количество
    total = soup.select_one(".catalog-count, .total-count, [class*='count']")
    print(f"Счётчик товаров: {total.get_text(strip=True) if total else 'не найден'}")

    browser.close()
