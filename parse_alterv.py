"""
Парсер таблицы с alterv.ru в CSV (открывается в Excel).
Использует Playwright для рендеринга JS-страницы.

Запуск: python parse_alterv.py
"""

import csv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://alterv.ru/catalog/vibroizolyatory/a00005_vibroizolyatory_tsilindricheskie_s_naruzhnoy_rezboy_tip_ec_a/"
OUT_FILE = "alterv_a00005.csv"


def parse_html(html: str):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_="flt-table")
    if not table:
        raise RuntimeError("Таблица flt-table не найдена!")

    # Заголовки
    thead = table.find("thead")
    col_headers = []
    if thead:
        for th in thead.find_all("th"):
            title_span = th.find("span", class_="flt-table__title")
            if title_span:
                col_headers.append(title_span.get_text(strip=True))
            else:
                col_headers.append(th.get_text(strip=True))

    # Убираем "Заказать" и пустые хвосты
    while col_headers and col_headers[-1] in ("Заказать", ""):
        col_headers.pop()

    # Строки
    tbody = table.find("tbody")
    rows = []
    for tr in (tbody or table).find_all("tr", class_="table_row"):
        cells = tr.find_all("td")
        row = []
        for i, td in enumerate(cells):
            if i == len(cells) - 1:  # кнопка "Заказать"
                continue

            # Наличие
            nal_cell = td.find("span", class_="nal_cell")
            if nal_cell:
                p1 = nal_cell.find("span", class_="p1")
                if p1:
                    row.append(p1.get_text(strip=True))
                else:
                    btn = nal_cell.find("button")
                    row.append(btn.get_text(strip=True) if btn else nal_cell.get_text(strip=True))
                continue

            # Цена
            price_div = td.find("div", class_="table_price")
            if price_div:
                price_val = price_div.get("price", "")
                row.append(price_val.replace(".", ",") if price_val else "")
                continue

            # Обычная ячейка
            span = td.find("span")
            row.append(span.get_text(strip=True) if span else td.get_text(strip=True))

        if row:
            rows.append(row)

    return col_headers, rows


def main():
    print(f"Открываю браузер и загружаю {URL} ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)

        # Ждём пока таблица заполнится данными
        try:
            page.wait_for_selector("tr.table_row", timeout=15000)
        except Exception:
            print("Предупреждение: строки таблицы не появились за 15 сек, пробуем всё равно...")

        html = page.content()
        browser.close()

    print("Страница загружена, парсю таблицу...")
    headers, rows = parse_html(html)

    print(f"Колонки ({len(headers)}): {headers}")
    print(f"Строк данных: {len(rows)}")

    if not rows:
        print("Строки не найдены!")
        return

    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"\nГотово! Сохранено в: {OUT_FILE}")
    print("Открывай в Excel — разделитель точка с запятой (;)")


if __name__ == "__main__":
    main()
