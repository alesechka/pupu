"""
Удаляет оригинальные PNG из папки если для них уже есть подпапка с частями.
"""
from pathlib import Path
import os

DIRS = [
    "table_screenshots_opory",
    "table_screenshots",
    "table_screenshots_clean",
    "table_screenshots_no_favorites",
    "table_screenshots_zamki",
    "table_screenshots_fiksatory",
    "table_screenshots_zashchelki",
    "table_screenshots_smazka",
    "table_screenshots_makhoviki",
    "table_screenshots_petli",
    "table_screenshots_rukoyatki2",
    "table_screenshots_ruchki_p",
    "table_screenshots_ruchki_z",
]

for dir_name in DIRS:
    d = Path(dir_name)
    if not d.exists():
        continue
    deleted = 0
    for png in sorted(d.glob("*.png")):
        # Если есть подпапка с таким же именем (без .png) — значит файл был нарезан
        subdir = d / png.stem
        if subdir.is_dir() and any(subdir.glob("*.png")):
            print(f"  Удаляю: {png.name}")
            png.unlink()
            deleted += 1
    if deleted:
        print(f"{dir_name}: удалено {deleted} файлов")
    else:
        print(f"{dir_name}: нечего удалять")

print("\nГотово.")
