"""Переносит последние 71 строку из alterv_opory.csv в alterv_opory_missing.csv"""
import csv
from pathlib import Path

MISSING_URLS = {
    "https://alterv.ru/catalog/plastiny_antiskolzheniya_dlya_opor/a00019_plastiny_antiskolzheniya_dlya_sharnirnykh_opor_20/",
    "https://alterv.ru/catalog/plastiny_antiskolzheniya_dlya_opor/pam_plastiny_antiskolzheniya_dlya_sharnirnykh_opor/",
    "https://alterv.ru/catalog/osnovaniya_dlya_opor/k0419_osnovaniya_sharnirnykh_opor_vibroizoliruyushchie_20/",
    "https://alterv.ru/catalog/opory_s_podvizhnym_vintom/k0420_opory_sharnirnye_vibroizoliruyushchie_15/",
    "https://alterv.ru/catalog/osnovaniya_dlya_opor/k0670_osnovaniya_opor_diskovye_vibroizoliruyushchie/",
    "https://alterv.ru/catalog/prostavki_raspornye/k0057_prostavki_raspornye_podvizhnye_na_4/",
}

with open("alterv_opory.csv", encoding="utf-8-sig") as f:
    reader = csv.reader(f, delimiter=";")
    headers = next(reader)
    rows = list(reader)

url_idx = headers.index("URL товара")

original_rows = [r for r in rows if r[url_idx] not in MISSING_URLS]
missing_rows = [r for r in rows if r[url_idx] in MISSING_URLS]

print(f"Оригинальных строк: {len(original_rows)}")
print(f"Недостающих строк: {len(missing_rows)}")

# Сохраняем оригинальный CSV без добавленных строк
with open("alterv_opory.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerow(headers)
    writer.writerows(original_rows)

# Создаём новый CSV только с недостающими
with open("alterv_opory_missing.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerow(headers)
    writer.writerows(missing_rows)

print("Готово.")
