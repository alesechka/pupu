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

---

## TASK 5 — Поддержка нескольких таблиц на странице товара

**Проблема:** на некоторых страницах несколько таблиц `flt-table` с разными заголовками.
Старый код использовал `soup.find(...)` — находил только первую.

**Решение:** заменили на `soup.find_all(...)` в обоих парсерах:
- `get_table_headers` — итерируется по всем таблицам, собирает уникальные заголовки
- `parse_product_rows` — для каждой таблицы строит свой `col_index`, добавляет строки

---

## TASK 6 — Парсинг демпферов

**Файлы:** `parse_dempfery.py`, `alterv_dempfery.csv`
**URL:** https://alterv.ru/catalog/dempfery/
**Результат:** 8 товаров, 22 строки, 13 колонок. AJAX нет.

---

## TASK 7 — Парсинг рукояток зажимных

**Файлы:** `parse_rukoyatki.py`, `alterv_rukoyatki.csv`
**URL:** https://alterv.ru/catalog/rukoyatki_zazhimnye/
**Результат:** 3 товара, 70 строк, 28 колонок. До 4 таблиц на странице. AJAX нет.

---

## TASK 8 — Парсинг рычагов зажимных

**Файлы:** `parse_rychagi.py`, `alterv_rychagi.csv`
**URL:** https://alterv.ru/catalog/rychagi_zazhimnye/
**Результат:** 39 товаров, 35 уникальных колонок. AJAX — 1 клик "Показать ещё".

---

## TASK 9 — Скриншоты таблиц

**Файлы:** `screenshot_tables.py`, `screenshot_tables_clean.py`

Скрипты делают PNG-скриншоты таблиц `flt-table` со страниц товаров.
Берут HTML таблицы, оборачивают в чистый HTML, открывают в Playwright,
измеряют реальный размер через `getBoundingClientRect`, выставляют viewport и скриншотят.
Таблица любого размера влезает целиком.

`screenshot_tables_clean.py` дополнительно:
- Удаляет строку "Сбросить фильтр"
- Обрезает колонки начиная с "Наличие" и правее
- Удаляет "В избранное" и иконку сердечка

Папки с результатами исключены из git (`.gitignore`):
`table_screenshots/`, `table_screenshots_clean/`, `table_screenshots_no_favorites/`, `table_screenshots_zamki/`

---

## TASK 10 — Парсинг замков поворотных (с пагинацией)

**Файлы:** `parse_zamki.py`, `alterv_zamki.csv`, `screenshot_zamki.py`
**URL:** https://alterv.ru/catalog/zamki_povorotnye/
**Результат:** 94 товара, 623 строки, 29 колонок.

**Особенность:** каталог разбит на 5 страниц пагинации (`PAGEN_2=1..5`).
На каждой странице дополнительно есть кнопка "Показать ещё".

---

## TASK 11 — Поддержка пагинации во всех парсерах

Все парсеры обновлены — добавлены общие хелперы:

### `_hide_popup(page)`
Скрывает попап геолокации через JS.

### `_click_show_more(page)`
Кликает "Показать ещё" в цикле пока кнопка есть.
После каждого клика ждёт появления новых товаров (до 15 сек).
Если кнопка временно исчезла — ждёт её повторного появления до 5 сек.

### `_get_pagination_urls(page) -> list`
Собирает URL всех страниц пагинации из `.module-pagination .nums a.dark_link`.

### `_collect_links(page, seen, links)`
Собирает ссылки на товары с текущей страницы в общий список (дубли через `seen`).

### `get_product_links(page)` — новая логика:
1. Загружает первую страницу каталога
2. Кликает "Показать ещё" до конца
3. Собирает URL страниц пагинации
4. Для каждой страницы пагинации — повторяет шаги 2-3
5. Возвращает полный список товаров

---

## TASK 12 — Тест пагинации

**Файл:** `test_pagination.py`

Проверяет что `get_product_links` каждого каталога находит ожидаемое количество товаров.
Результат последнего запуска: **6/6 OK**.

| Каталог         | Ожидалось | Найдено |
|-----------------|-----------|---------|
| vibroizolyatory | 12        | 12      |
| vibroopory      | 22        | 22      |
| dempfery        | 8         | 8       |
| rukoyatki       | 3         | 3       |
| rychagi         | 39        | 39      |
| zamki           | 94        | 94      |

---

## Структура функций парсеров

### `get_product_links(page)`
Загружает каталог, обходит пагинацию, возвращает список `(название, url)`.

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
- Попап геолокации перекрывает клики — всегда скрывать через JS перед кликами
- Некоторые каталоги имеют пагинацию (`PAGEN_2=N`) — обходить все страницы

---

## TASK 13 — Нарезка скриншотов > 299 КБ

**Файл:** `split_screenshots.py`

Делит PNG-файлы превышающие 299 КБ на части по границам строк таблицы (Pillow).
- Ширина сохраняется полностью
- Разрез только между строками (не внутри ячейки) — ищет горизонтальные серые линии
- Каждый большой файл → подпапка рядом с файлом
- Именование частей: `<имя_исходного_файла>_part_1.png`, `_part_2.png` и т.д.
- Исходный файл не трогается

Обрабатывает папки: `table_screenshots`, `table_screenshots_clean`, `table_screenshots_no_favorites`, `table_screenshots_zamki`.

---

## TASK 14 — Колонка "Применение HTML" во всех парсерах

**Файлы:** все парсеры (`parse_zamki.py`, `parse_alterv_all.py`, `parse_vibroopory.py`, `parse_dempfery.py`, `parse_rukoyatki.py`, `parse_rychagi.py`)

Добавлена функция `get_prim_html(page)` — кликает таб "Применение" (`a[href='#prim']`) через JS и возвращает `innerHTML` блока `#prim`.

В `main()` вызывается в проходе 1 после загрузки страницы товара, результат кешируется вместе с HTML как `(title, html, prim_html)`. В проходе 2 передаётся в `parse_product_rows(..., prim_html=prim_html)`.

`FIXED_COLS` обновлён: добавлена колонка `"Применение HTML"`.

---

## TASK 15 — Колонка "Описание" (скрин + HTML описание)

**Файлы:** `build_description_col.py`

Отдельный скрипт добавляет колонку "Описание" во все CSV.

**Содержимое колонки:**
```
<p><img src="https://promfurnitura.by/image/catalog/prom-furnitura/zamki/ИМЯ_ФАЙЛА.png" style="width: XXXpx;"></p>
... (для каждого скрина товара)
+ innerHTML блока #prim
```

**Матчинг скринов к товару:**
- Из URL товара извлекается код: токены slug до первого чисто-буквенного (транслит), склеенные без `_`
  - Пример: `.../k0518_zamki_...` → `k0518`
  - Пример: `.../a40101_063_a40105_zamki_...` → `a40101063a40105`
- Из имени файла скрина аналогично: `k0518_k0519_замки_..._table_1.png` → `k0518k0519`
- Используется **prefix-матчинг**: код `k0518` найдёт файлы с кодом `k0518`, `k0518k0519` и т.д.

Ширина в `style="width: XXXpx;"` — реальная ширина PNG (через Pillow).

---

## TASK 16 — Скрины для недостающих товаров

**Файл:** `screenshot_missing.py`

Автоматически находит товары без скринов (сравнивает коды из CSV с индексом файлов) и делает скрины для них по той же логике что `screenshot_zamki.py` (clean вариант).

Результат: 28 недостающих замков досняты, все CSV покрыты на 100%.

---

## TASK 17 — Сбор "Применение HTML" без перепарсинга

**Файл:** `fetch_prim_html.py`

Отдельный скрипт для заполнения колонки "Применение HTML" в существующих CSV без полного перепарсинга.

**Алгоритм:**
1. Собирает все уникальные URL из всех CSV (178 уникальных)
2. Для каждого URL: загружает страницу, кликает таб "Применение", забирает `innerHTML` блока `#prim`
3. Добавляет/обновляет колонку "Применение HTML" в каждом CSV
4. Колонка вставляется после "Фото дополнительные"

После запуска `fetch_prim_html.py` нужно перезапустить `build_description_col.py` чтобы колонка "Описание" подхватила новый `prim_html`.

**Результат:** все CSV покрыты на 100%, колонка "Описание" содержит img-теги скринов + HTML описания из вкладки "Применение".

---

## TASK 18 — Новая категория: фиксаторы поворотные

**Файлы:** `parse_fiksatory.py`, `screenshot_fiksatory.py`, `alterv_fiksatory.csv`
**URL каталога:** https://alterv.ru/catalog/fiksatory_povorotnye/

**Результат парсинга:** 16 товаров, 72 строки данных.

**Скриншоты:** `screenshot_fiksatory.py` — 20 скринов в `table_screenshots_fiksatory/` (папка в `.gitignore`). Все скрины ≤ 299 КБ, нарезка не потребовалась.

**Обновлённые скрипты:**
- `build_description_col.py` — добавлен `alterv_fiksatory.csv` в `CSV_FILES`, `table_screenshots_fiksatory` в `SCREENSHOT_DIRS`
- `fetch_prim_html.py` — добавлен `alterv_fiksatory.csv` в `CSV_FILES`
- `screenshot_missing.py` — добавлена новая папка и маппинг CSV→папка
- `.gitignore` — добавлена `table_screenshots_fiksatory/`

**Финальный запуск:**
- `fetch_prim_html.py`: 195 уникальных URL обработаны, `alterv_fiksatory.csv` обновлён (72 строки с `Применение HTML`)
- `build_description_col.py`: 164 кода, 581 файл, `alterv_fiksatory.csv` обновлён (73/73 строк с колонкой "Описание")

---

## TASK 19 — Новая категория: защёлки накидные

**Файлы:** `parse_zashchelki.py`, `screenshot_zashchelki.py`, `alterv_zashchelki.csv`
**URL каталога:** https://alterv.ru/catalog/zashchelki_nakidnye/

**Результат парсинга:** 53 товара, 444 строки, 73 уникальные колонки.

**Скриншоты:** `screenshot_zashchelki.py` — 109 скринов в `table_screenshots_zashchelki/` (папка в `.gitignore`). Все скрины ≤ 299 КБ, нарезка не потребовалась.

**Обновлённые скрипты:**
- `build_description_col.py` — добавлен `alterv_zashchelki.csv` в `CSV_FILES`, `table_screenshots_zashchelki` в `SCREENSHOT_DIRS`
- `fetch_prim_html.py` — добавлен `alterv_zashchelki.csv` в `CSV_FILES`
- `screenshot_missing.py` — добавлена новая папка и маппинг CSV→папка
- `split_screenshots.py` — добавлена `table_screenshots_zashchelki` в `SCREENSHOT_DIRS`
- `.gitignore` — добавлена `table_screenshots_zashchelki/`

**Финальный запуск:**
- `fetch_prim_html.py`: 248 уникальных URL обработаны, `alterv_zashchelki.csv` обновлён (444 строки с `Применение HTML`)
- `build_description_col.py`: 209 кодов, 680 файлов, `alterv_zashchelki.csv` обновлён (445/445 строк с колонкой "Описание")
