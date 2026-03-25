"""
Добавляет колонку "Бренд" в CSV файлы.
Берёт бренд из <p class="manufacturer"> на странице товара.
Работает по уникальным URL товара.
"""

import csv
import time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Файлы для обработки — добавляй сюда новые
CSV_FILES = [
    "alterv_opory.csv",
]


def _hide_popup(page):
    try:
        page.evaluate("""
            ['altasib_geobase_window','altasib_geobase_window_block'].forEach(id => {
                var el = document.getElementById(id); if (el) el.style.display = 'none';
            });
        """)
    except Exception:
        pass


def get_brand(html: str) -> str:
    """Извлекает название бренда из <p class="manufacturer">"""
    soup = BeautifulSoup(html, "html.parser")
    p = soup.find("p", class_="manufacturer")
    if not p:
        return ""
    a = p.find("a")
    return a.get_text(strip=True) if a else ""


def collect_unique_urls(csv_files: list) -> list:
    seen = set()
    urls = []
    for csv_file in csv_files:
        p = Path(csv_file)
        if not p.exists():
            continue
        with open(p, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f, delimiter=";"))
        if not rows:
            continue
        headers = rows[0]
        url_idx = headers.index("URL товара") if "URL товара" in headers else 1
        for row in rows[1:]:
            url = row[url_idx] if len(row) > url_idx else ""
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def update_csv(csv_path: str, brand_cache: dict):
    p = Path(csv_path)
    if not p.exists():
        return

    with open(p, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f, delimiter=";"))

    headers = rows[0]
    url_idx = headers.index("URL товара") if "URL товара" in headers else 1

    if "Бренд" not in headers:
        # Вставляем после "URL товара"
        insert_at = url_idx + 1
        headers.insert(insert_at, "Бренд")
        for row in rows[1:]:
            while len(row) < len(headers):
                row.append("")
            row.insert(insert_at, "")
        brand_idx = insert_at
    else:
        brand_idx = headers.index("Бренд")

    updated = 0
    for row in rows[1:]:
        url = row[url_idx] if len(row) > url_idx else ""
        if url and url in brand_cache:
            while len(row) <= brand_idx:
                row.append("")
            row[brand_idx] = brand_cache[url]
            updated += 1

    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"  {csv_path}: обновлено {updated} строк")


def main():
    urls = collect_unique_urls(CSV_FILES)
    print(f"Уникальных URL: {len(urls)}")

    brand_cache = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            try:
                page.goto(url, wait_until="commit", timeout=20000)
                try:
                    page.wait_for_selector("p.manufacturer", timeout=8000)
                except Exception:
                    pass
                _hide_popup(page)
                html = page.content()
                brand = get_brand(html)
                brand_cache[url] = brand
                print(f"  Бренд: {brand or '(не найден)'}")
            except Exception as e:
                print(f"  ОШИБКА: {e}")
                brand_cache[url] = ""
            time.sleep(0.2)

        browser.close()

    print("\nОбновляю CSV...")
    for csv_file in CSV_FILES:
        update_csv(csv_file, brand_cache)

    print("\nГотово.")


if __name__ == "__main__":
    main()
