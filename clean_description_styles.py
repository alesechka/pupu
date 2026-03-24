"""
Очищает HTML в колонке _DESCRIPTION_ — приводит к единому стилю.

Целевой формат:
  <p><img src="..." style="width: Xpx"></p>
  <span style="font-family: 'Open Sans', sans-serif">
    <h2><span style="font-size: 13pt">Заголовок</span></h2>
    <ul><li>текст</li></ul>
    <hr>
    ...
  </span>
"""

import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup, Tag, NavigableString

EXPORT_FILE = "product_export_0-100000_2026-03-25-0014.csv"
OPEN_SANS = "'Open Sans', sans-serif"
OPEN_SANS_STYLE = f"font-family: {OPEN_SANS}"


def clean_html(html: str) -> str:
    if not html:
        return html

    soup = BeautifulSoup(html, "html.parser")

    # --- Step 1: collect <img> tags (for the top) ---
    img_tags = soup.find_all("img")

    # --- Step 2: collect all content nodes (non-img) ---
    # We'll rebuild from scratch

    # Extract img info
    imgs_html = []
    for img in img_tags:
        style = img.get("style", "")
        w = re.search(r'width\s*:\s*\d+px', style)
        src = img.get("src", "")
        if src:
            w_style = w.group() if w else ""
            if w_style:
                imgs_html.append(f'<p><img src="{src}" style="{w_style}"></p>')
            else:
                imgs_html.append(f'<p><img src="{src}"></p>')

    # --- Step 3: collect content blocks (h2, h3, ul, hr, p with text) ---
    content_parts = []

    def process_node(node):
        if not isinstance(node, Tag):
            return
        name = node.name.lower()

        if name == "img":
            return  # already handled

        if name in ("h2", "h3"):
            text = " ".join(node.get_text().split())
            content_parts.append(f'<{name}><span style="font-size: 13pt">{text}</span></{name}>')

        elif name == "ul":
            items = []
            for li in node.find_all("li", recursive=False):
                li_text = " ".join(li.get_text().split())
                if li_text.strip():
                    items.append(f"<li>{li_text}</li>")
            if items:
                content_parts.append("<ul>" + "".join(items) + "</ul>")

        elif name == "hr":
            content_parts.append("<hr>")

        elif name == "p":
            # Skip p tags that only contain img or br
            children = [c for c in node.children if not (isinstance(c, NavigableString) and not c.strip())]
            non_img = [c for c in children if not (isinstance(c, Tag) and c.name in ("img", "br"))]
            if non_img:
                text = " ".join(node.get_text().split())
                if text:
                    content_parts.append(f"<p>{text}</p>")

        elif name in ("div", "section", "article"):
            for child in node.children:
                process_node(child)

        elif name == "span":
            # Top-level span (Open Sans wrapper) — process its children
            for child in node.children:
                process_node(child)

        elif name in ("ol",):
            items = []
            for li in node.find_all("li", recursive=False):
                li_text = li.get_text()
                if li_text.strip():
                    items.append(f"<li>{li_text}</li>")
            if items:
                content_parts.append("<ol>" + "".join(items) + "</ol>")

    for child in soup.children:
        process_node(child)

    # --- Step 4: assemble ---
    result = "".join(imgs_html)
    if content_parts:
        result += f'<span style="{OPEN_SANS_STYLE}">' + "".join(content_parts) + "</span>"

    return result


def main():
    p = Path(EXPORT_FILE)
    print(f"Читаю {EXPORT_FILE}...")
    with open(p, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        headers = next(reader)
        rows = list(reader)

    desc_idx = headers.index("_DESCRIPTION_")
    updated = 0

    for row in rows:
        if desc_idx >= len(row) or not row[desc_idx]:
            continue
        original = row[desc_idx]
        fixed = clean_html(original)
        if fixed != original:
            row[desc_idx] = fixed
            updated += 1

    print(f"Обработано строк: {updated}/{len(rows)}")

    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    print("Готово.")


if __name__ == "__main__":
    main()
