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


# Перевіряємо чи створено всі необхідні директорії
def ensure_dir(dir_path: Path):
    dir_path.mkdir(parents=True, exist_ok=True)


def ensure_parent_dir(file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)


# Зберігаємо файли локально заради пришвидшення обробки в мабутньому
def save_to_local_file(xmls):
    for xml in xmls:
        print(f"Зберігаю дані {xml["name"]}")
        response = requests.get(xml["url"], verify=False)
        response.raise_for_status()

        ensure_dir(settings.XML_RAW_PATH)
        with open(f"{settings.XML_RAW_PATH}/{xml["name"]}.xml", "wb") as f:
            f.write(response.content)


# Парсимо Yandex Market language для перетворення на придатний для OpenCart формат
def parse_from_yandex_market_language(file):
    items = list()

    try:
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
    except etree.XMLSyntaxError:
        print(f"{file} is not data file")

    return items


# ПРОХОДИМОСЯ ПО ВСІХ МАГАЗИНАХ САЙТИ ЯКИХ ТРЕБА ПАРСИТИ
def get_routes():
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
    
    ensure_parent_dir(settings.ROUTES_PATH)
    parser.json_to_file(settings.ROUTES_PATH, urls)


# ФУНКЦІЯ ЗБОРУ СИРИХ HTML-даних
def get_raw_html(routes, html_elements_to_parse, elem_to_click):
    for site in routes:
        products = list()
        for site_name in site.keys():
            urls = site[site_name]

            for url in urls:
                product = dict()
                product["url"] = url
                product["html"] = parser.stealth_data_load(URL=url, css_class=html_elements_to_parse, elem_to_click=elem_to_click)
                products.append(product)
        
        ensure_dir(settings.WEB_RAW_PATH)
        parser.json_to_file(f"{settings.WEB_RAW_PATH}{site_name}.xml", products)


# ВИКОНАННЯ ПРОГРАМИ
if __name__ == "__main__":
    print("\n------------------------------------------\nЗбір даних для MADHUNT\n------------------------------------------\n")

    while(True):
        try:
            option = input("\nОберіть опцію:\n\t1 - збереження та обробка XML\n\t2 - парсинг web-сайтів для збору даних\n\t3 - ТЕСТ (опція для розробника)\n\t4 - завершити\n")

            # Збираємо дані з XML
            if option == "1":
                
                # 1. Завантажуємо XML-вигрузки
                print("Зберігаю XML-вигрузки локально для майбутньої обробки...\n")
                start_time = time.time()

                save_to_local_file(settings.XMLS)

                # 2. Приводимо вигрузки до єдиного формату з Yandex Market language (вигрузки xml) у JSON
                print("Приводжу XML-вигрузки до загального формату...\n")

                folder_path = Path(settings.XML_RAW_PATH)
                files = [p for p in folder_path.rglob('*') if p.is_file()]

                items = list()
                for file in files:
                    items.extend(parse_from_yandex_market_language(str(file)))

                ensure_parent_dir(settings.XML_RESULT_PATH)
                parser.json_to_file(settings.XML_RESULT_PATH, items)

                end_time = time.time()
                print(f"\nЧас збереження даних: {(end_time - start_time) / 60:.2f} хв\n")
            
            # Збираємо дані з WEB
            elif option == "2":
                print("Вивантажую дані з магазину Control\n")
                start_time = time.time()

                # 1. Збираємо посилання на товари
                get_routes()

                # 2. Збираємо "сирі" HTML-дані
                routes = parser.json_from_file(settings.ROUTES_PATH)
                html_elements_to_parse = [".producttitle", ".pricemain i", ".product__descr .nov", ".slick-track a img", ".attr-td"]
                elem_to_click = ".specification__link"

                get_raw_html(routes=routes, html_elements_to_parse=html_elements_to_parse, elem_to_click=elem_to_click)

                # 3. Обробляємо зібрані сирі дані у відповідний формат

                end_time = time.time()
                print(f"\nЧас збереження даних: {(end_time - start_time) / 60:.2f} хв\n")

            # Збираємо "сирі" дані про товари
            elif option == "3":
                print("БЛОК ДЛЯ ТЕСТУВАННЯ")
                
                pass
            elif option == "4":
                break
            else:
                print("Неіснуюча опція!")
        except:
            print("EXCEPTION: помилка запуску програми.")