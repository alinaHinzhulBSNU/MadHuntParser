import time
import requests
import pandas as pd
from pathlib import Path
from lxml import etree

# імпортуємо налаштування та парсер
import settings
import parser

# Вимикаємо попередження
import warnings
warnings.filterwarnings("ignore")


# Зберігаємо файли локально заради пришвидшення обробки в мабутньому
def save_to_local_file(xmls):
    for xml in xmls:
        print(f"Зберігаю дані {xml["name"]}")
        response = requests.get(xml["url"], verify=False)
        response.raise_for_status()
        with open(f"DATA/raw_from_xml/{xml["name"]}.xml", "wb") as f:
            f.write(response.content)


# Парсимо Yandex Market language для перетворення на придатний для OpenCart формат
def parse_from_yandex_market_language(file):
    items = list()
    offers = etree.parse(file).getroot().xpath("./shop/offers/offer")     
    for offer in offers:
        item = dict()
        params = list()
        for field in offer:
            if field.tag != "param":
                item[field.tag] = field.text
            else:
                param = dict()
                param[field.attrib.get("name")] = field.text
                params.append(param)
        item["params"] = params
        items.append(item)

    return items


# ВИКОНАННЯ ПРОГРАМИ
if __name__ == "__main__":
    print("\n------------------------------------------\nЗбір даних для MADHUNT\n------------------------------------------\n")

    while(True):
        option = input("\nОберіть опцію:\n\t1 - локальне збереження XML\n\t2 - приведення вигрузок до єдиного формату\n\t3 - збереження даних з Web\n\t4 - завершити\n")

        if option == "1":

            # Завантажуємо XML-вигрузки
            print("Зберігаю XML-вигрузки локально для майбутньої обробки...\n")
            start_time = time.time()  # фіксуємо час початку збереження файлу
            save_to_local_file(settings.XMLS)
            end_time = time.time()  # фіксуємо час завершення збереження файлу
            print(f"\nЧас збереження даних: {(end_time - start_time) / 60:.2f} хв\n")
        
        elif option == "2":

            # Парсинг файлів Yandex Market language (вигрузки xml) у JSON
            # для того щоб сумістити з результатами парсингу сайтів і привести все до однорідного формату в БД
            print("Приводжу XML-вигрузки до загального формату...\n")
            folder_path = Path("DATA/raw_from_xml")
            files = [p for p in folder_path.rglob('*') if p.is_file() and str(p) != "DATA/raw_from_xml/.DS_Store"]

            items = list()
            for file in files:
                items.extend(parse_from_yandex_market_language(file))

            parser.json_to_file(settings.XML_RESULT_PATH, items)

        elif option == "3":
            
            print("Вивантажую дані з сайтів для майбутньої обробки...\n")
            start_time = time.time()  # фіксуємо час початку збереження файлу

            # ПРОХОДИМОСЯ ПО ВСІХ МАГАЗИНАХ САЙТИ ЯКИХ ТРЕБА ПАРСИТИ
            urls = list()
            for url in settings.URLS:

                # 1. Шукаємо всі доступні сторінки ДЛЯ КОЖНОГО З МАГАЗИНІВ
                pages_html = parser.stealth_data_load(url["url"], css_class=url["pagination_css_class"])
                pages = pages_html[0]["text"].split("\n")
                page_urls = [url["url"] + f"?page={page}" for page in pages]

                # 2. Шукаємо всі доступні посилання на товари НА КОЖНІЙ ЗІ СТОРІНОК
                product_urls = []
                for page_url in page_urls:
                    product_urls.extend([url["href"] for url in parser.stealth_data_load(page_url, css_class=".mpp-item-name a")])

                route = dict()
                route[url["name"]] = list(set(product_urls))
                urls.append(route)
            
            parser.json_to_file(settings.ROUTES_PATH, urls)
    
            end_time = time.time()  # фіксуємо час завершення збереження файлу
            print(f"\nЧас збереження даних: {(end_time - start_time) / 60:.2f} хв\n")

            # href uniquq
            # "img-responsive", src
            # "productdrive" by \n - ціна
            # "product__descr" - опис і далі
        elif option == "4":
            break
        else:
            print("Неіснуюча опція!")