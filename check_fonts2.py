import csv, re

files = [
    'alterv_vibroopory.csv', 'alterv_rukoyatki.csv', 'alterv_zamki.csv',
    'alterv_all.csv', 'alterv_dempfery.csv', 'alterv_rychagi.csv',
    'alterv_fiksatory.csv', 'alterv_zashchelki.csv', 'alterv_smazka.csv',
    'alterv_makhoviki.csv',
]

for f in files:
    try:
        with open(f, encoding='utf-8-sig') as fh:
            reader = csv.reader(fh, delimiter=';')
            headers = next(reader)
            rows = list(reader)
        if 'Описание' not in headers:
            print(f'{f}: нет колонки Описание')
            continue
        idx = headers.index('Описание')
        bad1 = sum(1 for r in rows if idx < len(r) and 'Open Sans&quot;' in r[idx])
        bad2 = sum(1 for r in rows if idx < len(r) and re.search(r"sans-serif;[A-Za-z&]", r[idx]))
        print(f'{f}: строк={len(rows)}, мусор_quot={bad1}, мусор_semicolon={bad2}')
        for r in rows:
            if idx < len(r) and ('Open Sans&quot;' in r[idx] or re.search(r"sans-serif;[A-Za-z&]", r[idx])):
                m = re.search(r'font-family[^"\'<]{0,120}', r[idx])
                if m:
                    print(f'  пример: {m.group()[:120]}')
                break
    except Exception as e:
        print(f'{f}: ошибка {e}')
