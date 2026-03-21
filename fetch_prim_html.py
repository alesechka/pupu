"""
Дополняет существующие CSV колонкой "Применение HTML".
Не перепарсит всё заново — только заходит на каждый уникальный URL товара,
кликает таб "Применение" и забирает innerHTML блока #prim.
"""

import csv
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

CSV_FILES = [
    "alterv_zamki.csv",
    "alterv_all.csv",
    "alterv_vibroopory.csv",
    "alterv_dempfery.csv",
    "alterv_rukoyatki.csv",
    "alterv_rychagi.csv",
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


def get_prim_html(page, url: str) -> str:
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
        _hide_popup(page)
        tab = page.query_selector("a[href='#prim']")
        if not tab:
            return ""
        page.evaluate("document.querySelector(\"a[href='#prim']\").click()")
        page.wait_for_selector("#prim.active, #prim.tab-pane_new", timeout=5000)
        html = page.evaluate("document.getElementById('prim') ? document.getElementById('prim').innerHTML : ''")
        return html.strip() if html else ""
    except Exception as e:
        print(f"    ОШИБКА: {e}")
        return ""


def collect_unique_urls(csv_files: list[str]) -> list[str]:
    seen = set()
    urls = []
    for csv_file in csv_files:
        p = Path(csv_file)
        if not p.exists():
            continue
        with open(p, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f, delimiter=";"))
        url_idx = rows[0].index("URL товара") if "URL товара" in rows[0] else 1
        for row in rows[1:]:
            url = row[url_idx] if len(row) > url_idx else ""
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def update_csv(csv_path: str, prim_cache: dict[str, str]):
    p = Path(csv_path)
    if not p.exists():
        return

    with open(p, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f, delimiter=";"))

    headers = rows[0]
    url_idx = headers.index("URL товара") if "URL товара" in headers else 1

    # Добавляем колонку если нет
    if "Применение HTML" not in headers:
        # Вставляем после "Фото дополнительные" если есть, иначе в конец
        try:
            insert_at = headers.index("Фото дополнительные") + 1
        except ValueError:
            insert_at = len(headers)
        headers.insert(insert_at, "Применение HTML")
        for row in rows[1:]:
            while len(row) < len(headers):
                row.append("")
            row.insert(insert_at, "")
        prim_idx = insert_at
    else:
        prim_idx = headers.index("Применение HTML")

    updated = 0
    for row in rows[1:]:
        url = row[url_idx] if len(row) > url_idx else ""
        if url and url in prim_cache:
            while len(row) <= prim_idx:
                row.append("")
            row[prim_idx] = prim_cache[url]
            updated += 1

    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"  {csv_path}: обновлено {updated} строк")


def main():
    urls = collect_unique_urls(CSV_FILES)
    print(f"Уникальных URL: {len(urls)}")

    prim_cache: dict[str, str] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            html = get_prim_html(page, url)
            prim_cache[url] = html
            if html:
                print(f"    OK ({len(html)} символов)")
            else:
                print(f"    (пусто)")
            time.sleep(0.2)

        browser.close()

    print("\nОбновляю CSV...")
    for csv_file in CSV_FILES:
        update_csv(csv_file, prim_cache)

    print("\nГотово.")


if __name__ == "__main__":
    main()
