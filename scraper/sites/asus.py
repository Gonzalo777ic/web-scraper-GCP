
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

CATEGORIES = [
    {"name": "ROG Zephyrus", "url": "https://www.asus.com/pe/laptops/for-gaming/rog-republic-of-gamers/filter?SubSeries=ROG-Zephyrus"},
    {"name": "ROG Flow", "url": "https://www.asus.com/pe/laptops/for-gaming/rog-republic-of-gamers/filter?SubSeries=ROG-Flow"},
    {"name": "ROG Strix", "url": "https://www.asus.com/pe/laptops/for-gaming/rog-republic-of-gamers/filter?SubSeries=ROG-Strix"}
]

def scroll_and_load_more(driver):
    """
    Scroll profundo + Clic en 'Mostrar más' para Asus.
    """
    print("   [Asus] Bajando y buscando botón 'Mostrar más'...")
    

    for i in range(3):

        last_height = driver.execute_script("return document.body.scrollHeight")
        step = 600
        for pos in range(0, last_height, step):
            driver.execute_script(f"window.scrollTo(0, {pos});")
            time.sleep(0.1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)



        try:

            btn = driver.find_element(By.CSS_SELECTOR, "div[class*='ShowMore__showMoreBtn']")
            if btn.is_displayed():
                print(f"   [Asus] Clic en 'Mostrar más' ({i+1})...")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(4) 
            else:
                break 
        except NoSuchElementException:
            break 

def extract_category_data(html_content, category_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []


    cards = soup.find_all('div', class_=re.compile(r'ProductCardNormalGrid__productCardContainer'))

    for card in cards:
        try:

            name_tag = card.find('h2')
            if not name_tag:
                link_heading = card.find('a', class_=re.compile(r'ProductCardNormalGrid__headingRow'))
                if link_heading: name_tag = link_heading.find('h2')
            
            name = name_tag.get_text(" ", strip=True) if name_tag else "Asus Desconocido"


            price = 0.0
            price_text = ""
            
            discount = card.find('div', class_=re.compile(r'ProductCardNormalGrid__priceDiscount'))
            regular = card.find('div', class_=re.compile(r'ProductCardNormalGrid__regularPrice'))
            generic = card.find('div', class_=re.compile(r'ProductCardNormalGrid__price__'))

            if discount: price_text = discount.get_text(strip=True)
            elif generic: price_text = generic.get_text(strip=True)
            elif regular: price_text = regular.get_text(strip=True)

            if price_text and "Agotado" not in price_text:
                clean_text = re.sub(r'[^\d.]', '', price_text)
                try: price = float(clean_text)
                except: price = 0.0


            img_url = None
            img_wrapper = card.find('div', class_=re.compile(r'ProductCardNormalGrid__imageWrapper'))
            if img_wrapper:
                img_tag = img_wrapper.find('img')
                if img_tag: img_url = img_tag.get('src')


            pid = name.replace(" ", "-").replace("/", "").upper()[:20]

            if price > 0:
                products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": img_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": "Asus"
                })

        except Exception:
            continue
            
    return products

def scrape(driver):
    all_products = []
    print(f"--- Scrapeando ASUS ({len(CATEGORIES)} categorías) ---")

    for cat in CATEGORIES:
        print(f"   [Asus] Procesando: {cat['name']}...")
        try:
            driver.get(cat['url'])
            
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='ProductCardNormalGrid__productCardContainer']"))
                )
            except TimeoutException:
                print(f"   [Asus] Timeout en {cat['name']}. Continuando...")


            scroll_and_load_more(driver)
            
            current_products = extract_category_data(driver.page_source, cat['name'])
            print(f"   [Asus] Encontrados: {len(current_products)}")
            
            all_products.extend(current_products)
            time.sleep(2)

        except Exception as e:
            print(f"   [Asus] Error en {cat['name']}: {e}")

    return all_products