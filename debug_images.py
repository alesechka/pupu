from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://alterv.ru/catalog/rychagi_zazhimnye/', wait_until='networkidle', timeout=60000)
    time.sleep(2)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, 'html.parser')

btn = soup.select_one('.ajax_load_btn')
print('AJAX btn:', btn)

items = soup.select('.catalog_item_wrapp .item-title a')
print('Items found:', len(items))
for a in items:
    print(' -', a.get_text(strip=True), '|', a.get('href'))
