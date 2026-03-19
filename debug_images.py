from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://alterv.ru/catalog/vibroopory/a00017_vibroopory_rezinometallicheskie_reguliruemye_s_kryshkoy/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, "html.parser")

print("=== ОСНОВНЫЕ (slick-slide) ===")
for div in soup.select(".slick-slide img"):
    print(" ", div.get("src"))

print("\n=== ДОПОЛНИТЕЛЬНЫЕ (fancy/drawings) ===")
for a in soup.select("a[data-fancybox-group]"):
    print(f"  group={a.get('data-fancybox-group')} href={a.get('href')}")

print("\n=== ВСЕ a с popup_link ===")
for a in soup.select("a.popup_link"):
    print(f"  href={a.get('href')}")
