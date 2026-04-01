"""
Переименовывает все PNG файлы во всех папках со скриншотами:
кириллица → транслитерация (латиница).
Также переименовывает подпапки с частями (_part_N).
"""

import os, re
from pathlib import Path

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

DIRS = [
    "table_screenshots",
    "table_screenshots_clean",
    "table_screenshots_no_favorites",
    "table_screenshots_zamki",
    "table_screenshots_fiksatory",
    "table_screenshots_zashchelki",
    "table_screenshots_smazka",
    "table_screenshots_makhoviki",
    "table_screenshots_opory",
    "table_screenshots_petli",
    "table_screenshots_rukoyatki2",
    "table_screenshots_ruchki_p",
    "table_screenshots_ruchki_z",
    "table_screenshots_zazhimy",
    "table_screenshots_teleskop",
    "table_screenshots_fiksatory2",
    "table_screenshots_schetchiki",
    "table_screenshots_sharnirnye",
    "table_screenshots_magnity",
]

def transliterate(text):
    return ''.join(TRANSLIT.get(c, c) for c in text)

def needs_translit(name):
    return any(c in TRANSLIT for c in name)

def rename_file(f: Path) -> Path:
    """Переименовывает файл если в имени есть кириллица. Возвращает новый Path."""
    if not needs_translit(f.name):
        return f
    new_name = transliterate(f.name)
    new_path = f.parent / new_name
    if new_path != f and not new_path.exists():
        f.rename(new_path)
        return new_path
    return f

def rename_dir(d: Path) -> Path:
    """Переименовывает папку если в имени есть кириллица."""
    if not needs_translit(d.name):
        return d
    new_name = transliterate(d.name)
    new_path = d.parent / new_name
    if new_path != d and not new_path.exists():
        d.rename(new_path)
        return new_path
    return d

total_renamed = 0

for dir_name in DIRS:
    d = Path(dir_name)
    if not d.exists():
        continue

    renamed_in_dir = 0

    # Сначала переименовываем файлы в подпапках
    for sub in sorted(d.iterdir()):
        if sub.is_dir():
            for f in sorted(sub.glob("*.png")):
                new_f = rename_file(f)
                if new_f != f:
                    renamed_in_dir += 1
            # Переименовываем саму подпапку
            rename_dir(sub)

    # Потом файлы в корне папки
    for f in sorted(d.glob("*.png")):
        new_f = rename_file(f)
        if new_f != f:
            renamed_in_dir += 1

    if renamed_in_dir:
        print(f"{dir_name}: переименовано {renamed_in_dir} файлов")
    else:
        print(f"{dir_name}: нечего переименовывать")
    total_renamed += renamed_in_dir

print(f"\nВсего переименовано: {total_renamed}")
