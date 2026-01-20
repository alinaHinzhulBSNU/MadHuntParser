import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import settings


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
    # service = Service(executable_path=str(settings.CHROMEDRIVER_PATH))

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
def stealth_data_load(URL, css_class: list[str] | str | None = None, elem_to_click: str | None = None, timeout: int = 30):
    driver = setup_driver()
    driver.get(URL)

    wait = WebDriverWait(driver, timeout)

    # Для тих випадків коли потрібно клікнути кудись щоб побачити необхідні елементи
    try:
        if elem_to_click:
            wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, elem_to_click))
            ).click()
    except TimeoutException:
        print(f"Не клікаємо на кнопку через її відсутність ( {URL} )")

    # Формування CSS-селектора
    if css_class is None:
        selector = "*"
    elif isinstance(css_class, list):
        # '.class1, .class2, div[data-x]'
        selector = ", ".join(css_class)
    else:
        selector = css_class

    # Парсинг HTML-елементів
    try:
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, selector)
            )
        )
    except TimeoutException:
        print(f"EXCEPTION: не вдається спарсити html-елемент ( {URL} )")

    # Збір даних одним JS-викликом
    records = driver.execute_script(
        """
        const elements = document.querySelectorAll(arguments[0]);
        return Array.from(elements).map(el => {
            const attrs = {};
            for (const attr of el.attributes) {
                attrs[attr.name] = attr.value;
            }
            return {
                ...attrs,
                text: el.innerText
            };
        });
        """,
        selector
    )

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