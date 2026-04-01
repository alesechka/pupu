import csv, re
rows = list(csv.reader(open('alterv_rukoyatki.csv', encoding='utf-8-sig'), delimiter=';'))
desc = rows[2][rows[0].index('Описание')]
fonts = list(set(re.findall(r'font-family[^;]+', desc)))[:5]
for f in fonts:
    print(f.strip())
