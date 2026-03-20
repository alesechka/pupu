# Project Log — alterv.ru Parser

## Проект
Парсинг каталогов сайта https://alterv.ru в CSV.
Репозиторий: https://github.com/alesechka/pupu.git

---

## TASK 1 — Парсинг одной страницы товара

**Файлы:** `parse_alterv.py`, `alterv_a00005.csv`

Написан парсер одной страницы товара через Playwright (JS-рендеринг).
Парсит таблицу `flt-table`. Результат в CSV.

**Настройки CSV:** разделитель `;`, кодировка `utf-8-sig` (для Excel).

---

## TASK 2 — Парсинг всего каталога виброизоляторов

**Файлы:** `parse_alterv_all.py`, `alterv_all.csv`
**URL каталога:** https://alterv.ru/catalog/vibroizolyatory/

**Алгоритм (2 прохода):**
1. Проход 1 — заходим в каждый товар, собираем все уникальные заголовки таблиц
2. Проход 2 — парсим строки из кэша HTML, маппим по заголовкам в единый CSV

**Результат:** 12 товаров, 220 строк, 19 уникальных колонок.

**Колонки фото:**
- `Фото основные` — ссылки из `a[data-fancybox-group="item_slider"]`
- `Фото дополнительные` — ссылки из `a[data-fancybox-group="drawings"]`
- Несколько URL через запятую

---

## TASK 3 — Парсинг каталога виброопор (с AJAX)

**Файлы:** `parse_vibroopory.py`, `alterv_vibroopory.csv`
**URL каталога:** https://alterv.ru/catalog/vibroopory/

**Особенности:**
- Кнопка "Показать еще" (`.ajax_load_btn`) — эмулируем клики через `page.evaluate()` (JS-клик), потому что попап геолокации перекрывает обычный `.click()`
- Попап геолокации скрываем через JS: `document.getElementById('altasib_geobase_window').style.display='none'`

**Результат:** 22 товара, 222 строки, 43 уникальные колонки.

---

## TASK 4 — Push на GitHub

**Репо:** https://github.com/alesechka/pupu.git

**Важно:** Git не в PATH, использовать полный путь:
```
& "C:\Program Files\Git\cmd\git.exe" <команда>
```

Коммиты:
- `f16dc25` — add images columns to both parsers and csvs
- `2110fe8` — support multiple flt-table per product page

---

## TASK 5 — Поддержка нескольких таблиц на странице товара

**Проблема:** на некоторых страницах несколько таблиц `flt-table` с разными заголовками.
Старый код использовал `soup.find(...)` — находил только первую.

**Решение:** заменили на `soup.find_all(...)` в обоих парсерах:
- `get_table_headers` — итерируется по всем таблицам, собирает уникальные заголовки
- `parse_product_rows` — для каждой таблицы строит свой `col_index`, добавляет строки

Изменения в: `parse_alterv_all.py`, `parse_vibroopory.py`

---

## Структура функций парсеров

### `get_product_links(page)`
Загружает каталог, возвращает список `(название, url)`.

### `get_images(html) -> (main_imgs_str, extra_imgs_str)`
Ищет `a[data-fancybox-group]`:
- `item_slider` → основные фото
- `drawings` → дополнительные фото
Возвращает строки URL через запятую.

### `get_table_headers(html) -> list`
Находит все `table.flt-table`, собирает уникальные заголовки из `thead > th`.
Пропускает колонку "Заказать".

### `parse_product_rows(html, category, url, all_cols) -> list`
Для каждой таблицы строит маппинг `{имя_колонки: индекс_td}`.
Парсит `tr.table_row`, извлекает значения ячеек:
- `span.nal_cell` → наличие
- `div.table_price[price]` → цена (заменяет `.` на `,`)
- иначе → текст span или td

### `main()`
1. Загружает каталог, получает ссылки
2. Проход 1: обходит все товары, кэширует HTML, собирает заголовки
3. Проход 2: парсит строки из кэша
4. Пишет CSV

---

## Технический стек
- Python 3
- `playwright` (Chromium, headless) — JS-рендеринг
- `beautifulsoup4` — парсинг HTML
- `csv` — запись результатов

---

## Известные нюансы
- Сайт использует Slick Slider для фото — картинки появляются только после JS-рендеринга
- `networkidle` + `wait_for_selector("tr.table_row")` достаточно для загрузки таблиц
- Слайдер клонирует слайды (`.slick-cloned`) — дубли отфильтрованы через `seen` set в `get_images`
- Git в Windows не в PATH — всегда использовать полный путь к git.exe
