"""
Делит все PNG файлы в папке на подпапки по 20 штук.
Файлы из подпапок (уже нарезанные части) тоже учитываются.
"""
import os, shutil
from pathlib import Path

TARGET_DIR = "table_screenshots_fiksatory2"
BATCH_SIZE = 20

d = Path(TARGET_DIR)

# Собираем все PNG — и из корня и из подпапок
all_files = []
for f in sorted(d.glob("*.png")):
    all_files.append(f)
for sub in sorted(d.iterdir()):
    if sub.is_dir():
        for f in sorted(sub.glob("*.png")):
            all_files.append(f)

print(f"Всего файлов: {len(all_files)}")
print(f"Будет папок: {(len(all_files) + BATCH_SIZE - 1) // BATCH_SIZE}")

# Создаём подпапки batch_001, batch_002, ... и перемещаем файлы
for i, f in enumerate(all_files):
    batch_num = i // BATCH_SIZE + 1
    batch_dir = d / f"batch_{batch_num:03d}"
    batch_dir.mkdir(exist_ok=True)
    dest = batch_dir / f.name
    if f.parent != batch_dir:
        shutil.move(str(f), str(dest))

# Удаляем пустые подпапки (старые нарезанные)
for sub in sorted(d.iterdir()):
    if sub.is_dir() and not sub.name.startswith("batch_"):
        try:
            sub.rmdir()  # удалит только если пустая
        except: pass

print("Готово.")
