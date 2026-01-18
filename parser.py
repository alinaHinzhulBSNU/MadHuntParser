import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException


# НАЛАШТОВАНО ДЛЯ УНИКНЕННЯ БЛОКУВАННЯ
def setup_driver():

    # OPTIONS
    options = webdriver.ChromeOptions()

    options.add_argument("--lang=uk-UA,uk,ru-RU,ru,en-US,en")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # SERVICE
    service = Service(ChromeDriverManager().install())

    # DRIVER
    driver = webdriver.Chrome(service=service, options=options)

    stealth(driver,
            languages=["uk-UA", "uk", "ru-RU", "ru", "en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris Xe Graphics",
            fix_hairline=True,
        )
    
    # TIME ZONE
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "Europe/Kyiv"})
    
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
    """)

    return driver


# WEB SCRAPING
def stealth_data_load(URL, css_class=None, tag=None, click=None):
    driver = setup_driver()
    driver.get(URL)

    # Для тих випадків коли потрібно клікнути кудись щоб побачити необхідні елементи
    '''if click == "SPECIFICATION":
        specs_elem = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "js-article-info-header"))
        )
        specs_elem.click()
    elif click == "COLLECTIONS":
        elem = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "collection"))
        )
        elem.click()
    time.sleep(10)'''

    # Елемент де збережено дані в таблиці з результатами
    if not css_class and not tag:
        all_elements_web = driver.find_elements(By.XPATH, "//*")
    elif css_class and not tag:
        all_elements_web = WebDriverWait(driver, 100).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, css_class)
                )
        )
    elif not css_class and tag:
        all_elements_web = WebDriverWait(driver, 100).until(
                EC.presence_of_all_elements_located(
                    (By.TAG_NAME, tag)
                )
        )
    
    records = list()
    
    for element_web in all_elements_web:
        record = dict()

        try:
            attributes_dict = driver.execute_script(
                'var items = {}; '
                'for (index = 0; index < arguments[0].attributes.length; ++index) ' \
                '{ items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; ' \
                'return items;',
                element_web
            )

            for attribute in attributes_dict:
                record[attribute] = element_web.get_attribute(attribute)
            record["text"] = element_web.text

            records.append(record)
        except:
            pass

    driver.quit()

    return records


# ЗБЕРЕЖЕННЯ ДАНИХ ДО ФАЙЛУ JSON З МЕТОЮ ПОДАЛЬШОЇ ОБРОБКИ
def json_to_file(path, list):
    with open(path, "w") as file:
        json.dump(list, file, ensure_ascii = False, indent=4)


# ЧИТАННЯ ДАНИХ З ФАЙЛУ З МЕТОЮ ПОДАЛЬШОЇ ОБРОБКИ
def json_from_file(path):
    with open(path, "r") as file:
        return json.load(file)