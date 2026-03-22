"""
Делит PNG-скриншоты таблиц превышающие 299 КБ на части.
- Ширина сохраняется полностью
- Разрез только между строками (не внутри ячейки)
- Каждый файл > 299 КБ → отдельная папка <имя_файла_без_расширения>/part_1.png, part_2.png ...
- Исходный файл не трогается

Использует Pillow для работы с изображениями.
Алгоритм определения границ строк: ищет горизонтальные линии (строки пикселей),
где цвет близок к цвету границы таблицы (#cccccc / серый).
"""

import os
import sys
import io
from pathlib import Path
from PIL import Image

MAX_BYTES = 299 * 1024  # 299 КБ
# Папки со скриншотами для обработки
SCREENSHOT_DIRS = [
    "table_screenshots",
    "table_screenshots_clean",
    "table_screenshots_no_favorites",
    "table_screenshots_zamki",
    "table_screenshots_fiksatory",
    "table_screenshots_zashchelki",
]


def is_row_separator(img: Image.Image, y: int, threshold: int = 30) -> bool:
    """
    Проверяет, является ли строка пикселей y границей строки таблицы.
    Граница — строка где большинство пикселей светло-серые (цвет border таблицы).
    """
    width = img.width
    pixels = img.load()
    gray_count = 0
    sample_step = max(1, width // 50)  # сэмплируем каждые N пикселей

    for x in range(0, width, sample_step):
        r, g, b = pixels[x, y][:3]
        # Светло-серый: все каналы близки и в диапазоне 180-220
        if abs(r - g) < threshold and abs(g - b) < threshold and 160 <= r <= 230:
            gray_count += 1

    total_samples = len(range(0, width, sample_step))
    return gray_count / total_samples > 0.5


def find_row_boundaries(img: Image.Image) -> list[int]:
    """
    Возвращает список Y-координат где можно безопасно разрезать изображение.
    Это строки-разделители между рядами таблицы.
    """
    boundaries = [0]
    height = img.height
    last_was_sep = False

    for y in range(height):
        sep = is_row_separator(img, y)
        if sep and not last_was_sep:
            boundaries.append(y)
        last_was_sep = sep

    boundaries.append(height)
    return boundaries


def png_bytes(img: Image.Image) -> int:
    """Возвращает размер PNG в байтах без сохранения на диск."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.tell()


def split_image(img: Image.Image, boundaries: list[int]) -> list[Image.Image]:
    """
    Делит изображение на части так, чтобы каждая часть <= MAX_BYTES.
    Разрезает только по границам из списка boundaries.
    """
    parts = []
    start = 0
    current_end_idx = 1  # индекс в boundaries

    while current_end_idx < len(boundaries):
        # Пробуем добавить как можно больше строк в текущую часть
        best_end_idx = current_end_idx
        for i in range(current_end_idx, len(boundaries)):
            candidate = img.crop((0, boundaries[start], img.width, boundaries[i]))
            if png_bytes(candidate) <= MAX_BYTES:
                best_end_idx = i
            else:
                break

        # Если даже один сегмент не влезает — берём его как есть (минимальный кусок)
        if best_end_idx == current_end_idx - 1 or best_end_idx < current_end_idx:
            best_end_idx = current_end_idx

        end_y = boundaries[best_end_idx]
        start_y = boundaries[start]

        if end_y > start_y:
            part = img.crop((0, start_y, img.width, end_y))
            parts.append(part)

        # Ищем следующий start — первая граница после best_end_idx
        start = best_end_idx
        current_end_idx = best_end_idx + 1

    return parts


def process_file(png_path: Path):
    size = png_path.stat().st_size
    if size <= MAX_BYTES:
        return  # файл в норме

    print(f"  Делю: {png_path.name} ({size // 1024} КБ)")

    img = Image.open(png_path).convert("RGB")
    boundaries = find_row_boundaries(img)
    print(f"    Найдено границ строк: {len(boundaries) - 2}")

    parts = split_image(img, boundaries)
    print(f"    Частей: {len(parts)}")

    if len(parts) <= 1:
        print(f"    Не удалось разделить (слишком мало границ), пропускаем")
        return

    # Создаём папку рядом с файлом
    out_dir = png_path.parent / png_path.stem
    out_dir.mkdir(exist_ok=True)

    stem = png_path.stem  # имя исходного файла без расширения
    for i, part in enumerate(parts, 1):
        out_path = out_dir / f"{stem}_part_{i}.png"
        part.save(out_path, format="PNG")
        part_size = out_path.stat().st_size
        print(f"    {out_path.name} — {part.width}x{part.height}px, {part_size // 1024} КБ")


def process_dir(dir_path: str):
    p = Path(dir_path)
    if not p.exists():
        return

    png_files = sorted(p.glob("*.png"))
    if not png_files:
        return

    print(f"\nПапка: {dir_path} ({len(png_files)} файлов)")
    for f in png_files:
        process_file(f)


def main():
    dirs = sys.argv[1:] if len(sys.argv) > 1 else SCREENSHOT_DIRS

    for d in dirs:
        process_dir(d)

    print("\nГотово.")


if __name__ == "__main__":
    main()
