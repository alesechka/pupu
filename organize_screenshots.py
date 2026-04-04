"""
1. Нарезает PNG > 249 КБ на части (по строкам таблицы)
2. Удаляет оригиналы нарезанных файлов
3. Делит все PNG в каждой папке на подпапки batch_001, batch_002, ... по 20 файлов
"""

import os, io, shutil
from pathlib import Path
from PIL import Image

MAX_BYTES = 249 * 1024
BATCH_SIZE = 20

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
    "table_screenshots_krepezh",
    "table_screenshots_truby",
    "table_screenshots_profili",
    "table_screenshots_transport",
]


def png_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.tell()


def is_row_separator(img, y, threshold=30):
    width = img.width
    pixels = img.load()
    gray_count = 0
    sample_step = max(1, width // 50)
    for x in range(0, width, sample_step):
        r, g, b = pixels[x, y][:3]
        if abs(r - g) < threshold and abs(g - b) < threshold and 160 <= r <= 230:
            gray_count += 1
    total_samples = len(range(0, width, sample_step))
    return gray_count / total_samples > 0.5


def find_row_boundaries(img):
    boundaries = [0]
    last_was_sep = False
    for y in range(img.height):
        sep = is_row_separator(img, y)
        if sep and not last_was_sep:
            boundaries.append(y)
        last_was_sep = sep
    boundaries.append(img.height)
    return boundaries


def split_image(img, boundaries):
    parts = []
    start = 0
    current_end_idx = 1
    while current_end_idx < len(boundaries):
        best_end_idx = current_end_idx
        for i in range(current_end_idx, len(boundaries)):
            candidate = img.crop((0, boundaries[start], img.width, boundaries[i]))
            if png_bytes(candidate) <= MAX_BYTES:
                best_end_idx = i
            else:
                break
        if best_end_idx < current_end_idx:
            best_end_idx = current_end_idx
        end_y = boundaries[best_end_idx]
        start_y = boundaries[start]
        if end_y > start_y:
            part = img.crop((0, start_y, img.width, end_y))
            parts.append(part)
        start = best_end_idx
        current_end_idx = best_end_idx + 1
    return parts


def process_split(png_path: Path) -> bool:
    """Нарезает файл если > MAX_BYTES. Возвращает True если нарезал."""
    if png_path.stat().st_size <= MAX_BYTES:
        return False
    print(f"  Режу: {png_path.name} ({png_path.stat().st_size // 1024} КБ)")
    try:
        img = Image.open(png_path).convert("RGB")
        boundaries = find_row_boundaries(img)
        parts = split_image(img, boundaries)
        if len(parts) <= 1:
            print(f"    Не удалось разделить, пропускаем")
            return False
        out_dir = png_path.parent / png_path.stem
        out_dir.mkdir(exist_ok=True)
        stem = png_path.stem
        for i, part in enumerate(parts, 1):
            out_path = out_dir / f"{stem}_part_{i}.png"
            part.save(out_path, format="PNG")
            print(f"    {out_path.name} — {part.width}x{part.height}px, {out_path.stat().st_size // 1024} КБ")
        png_path.unlink()
        return True
    except Exception as e:
        print(f"    ОШИБКА при нарезке {png_path.name}: {e}")
        return False


def collect_all_pngs(d: Path):
    """Собирает все PNG из папки и всех подпапок."""
    files = []
    for f in sorted(d.glob("*.png")):
        files.append(f)
    for sub in sorted(d.iterdir()):
        if sub.is_dir():
            for f in sorted(sub.glob("*.png")):
                files.append(f)
            # Рекурсивно в подподпапках (batch внутри batch)
            for subsub in sorted(sub.iterdir()):
                if subsub.is_dir():
                    for f in sorted(subsub.glob("*.png")):
                        files.append(f)
    return files


def batch_into_dirs(d: Path, all_files):
    """Перемещает все файлы в batch_001, batch_002, ... по BATCH_SIZE штук."""
    # Удаляем старые batch_ папки если есть
    for sub in sorted(d.iterdir()):
        if sub.is_dir() and sub.name.startswith("batch_"):
            shutil.rmtree(sub)

    for i, f in enumerate(all_files):
        batch_num = i // BATCH_SIZE + 1
        batch_dir = d / f"batch_{batch_num:03d}"
        batch_dir.mkdir(exist_ok=True)
        dest = batch_dir / f.name
        if f.exists() and f.parent != batch_dir:
            try:
                shutil.move(str(f), str(dest))
            except Exception as e:
                print(f"    Ошибка перемещения {f.name}: {e}")

    # Удаляем пустые подпапки (старые нарезанные)
    for sub in sorted(d.iterdir()):
        if sub.is_dir() and not sub.name.startswith("batch_"):
            try:
                sub.rmdir()
            except: pass


for dir_name in DIRS:
    d = Path(dir_name)
    if not d.exists():
        continue

    print(f"\n=== {dir_name} ===")

    # Шаг 1: нарезаем большие файлы ТОЛЬКО в корне папки (не в подпапках)
    split_count = 0
    for f in sorted(d.glob("*.png")):
        if process_split(f):
            split_count += 1

    if split_count:
        print(f"  Нарезано: {split_count} файлов")

    # Шаг 2: собираем все PNG и делим на batch-папки
    all_files = collect_all_pngs(d)
    if not all_files:
        print(f"  Файлов нет, пропускаем")
        continue

    batch_into_dirs(d, all_files)
    batches = (len(all_files) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"  Файлов: {len(all_files)}, папок batch: {batches}")

print("\nГотово.")
