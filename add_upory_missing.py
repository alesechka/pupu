"""Добавляет 1 недостающий товар в alterv_upory.csv и делает скрин."""
import csv, time, os, re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pathlib import Path

MISSING_URL = "https://alterv.ru/catalog/vinty_nazhimnye/k0290_upory_podvizhnye_rezbovye_s_uplotnitelnym_koltsom/"
BASE_URL = "https://alterv.ru"
CSV_FILE = "alterv_upory.csv"
SCREENSHOT_DIR = "table_screenshots_upory"

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

HTML_TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:16px;background:#fff;font-family:Arial,sans-serif;font-size:13px;}}
table{{border-collapse:collapse;white-space:nowrap;}}
th,td{{border:1px solid #ccc;padding:6px 10px;text-align:left;}}
thead th{{background:#f0f0f0;font-weight:bold;}}
tr:nth-child(even){{background:#fafafa;}}
</style></head><body>{table_html}</body></html>"""

def transliterate(text):
    return ''.join(TRANSLIT.get(c, c) for c in text)

def slugify(text):
    text = transliterate(text.strip().lower())
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text)
    return text[:60]

def col_should_cut(col_text):
    col = col_text.lower().strip()
    return col.startswith("наличие") or col.startswith("цена") or col.startswith("стоимость")

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
        col = (span.get_text(strip=True) if span else th.get_text(strip=True))
        if col_should_cut(col): cut_index = i; break
    if cut_index is None: return
    for th in headers[cut_index:]: th.decompose()
    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            for td in tr.find_all("td")[cut_index:]: td.decompose()

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

def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    p = Path(CSV_FILE)
    with open(p, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        headers = next(reader)
        existing_rows = list(reader)

    fixed_count = 7
    all_cols = headers[fixed_count:]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(MISSING_URL, wait_until="commit", timeout=60000)
        try: page.wait_for_selector("tr.table_row", timeout=15000)
        except: pass
        _hide_popup(page)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else "K0290"
        prim_html = get_prim_html(page)
        breadcrumb = get_breadcrumbs(html)
        brand = get_brand(html)
        slug = slugify(title)
        print(f"Товар: {title} | {brand}")

        # Скрины
        tables = soup.find_all("table", class_="flt-table")
        for i, table in enumerate(tables, 1):
            clean_table(table)
            full_html = HTML_TEMPLATE.format(table_html=str(table))
            encoded = full_html.replace("\\","\\\\").replace("`","\\`").replace("${","\\${")
            page.evaluate(f"document.open();document.write(`{encoded}`);document.close();")
            page.wait_for_load_state("domcontentloaded")
            dims = page.evaluate("()=>{var t=document.querySelector('table');if(!t)return{width:1200,height:600};var r=t.getBoundingClientRect();return{width:Math.ceil(r.width)+32,height:Math.ceil(r.height)+32};}")
            w, h = max(dims["width"], 400), max(dims["height"], 100)
            page.set_viewport_size({"width": w, "height": h})
            out_path = os.path.join(SCREENSHOT_DIR, f"{slug}_table_{i}.png")
            page.screenshot(path=out_path, full_page=True)
            print(f"  скрин {i}: {slug}_table_{i}.png ({os.path.getsize(out_path)//1024} КБ)")

        browser.close()

    # Парсим строки
    main_imgs, extra_imgs = get_images(html)
    new_rows = []
    for table in soup.find_all("table", class_="flt-table"):
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
            row = [title, MISSING_URL, brand, breadcrumb, main_imgs, extra_imgs, prim_html]
            for col_name in all_cols:
                row.append(get_cell(col_index.get(col_name, -1)))
            new_rows.append(row)

    print(f"Новых строк: {len(new_rows)}")
    all_rows = existing_rows + new_rows
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(all_rows)
    print(f"Итого строк: {len(all_rows)}")

if __name__ == "__main__":
    main()
