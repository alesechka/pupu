import csv, re

with open('alterv_fiksatory.csv', encoding='utf-8-sig') as f:
    reader = csv.reader(f, delimiter=';')
    headers = next(reader)
    url_idx = headers.index('URL товара')
    desc_idx = headers.index('Описание')
    seen = set()
    for row in reader:
        url = row[url_idx] if len(row) > url_idx else ''
        if url in seen:
            continue
        seen.add(url)
        if 'a40102' in url.lower():
            desc = row[desc_idx] if len(row) > desc_idx else ''
            imgs = re.findall(r'<img ', desc)
            slug = url.rstrip('/').split('/')[-1]
            print(f'{slug}: {len(imgs)} картинок')
