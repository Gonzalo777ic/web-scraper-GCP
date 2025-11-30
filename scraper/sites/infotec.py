
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.infotec.com.pe/10-laptop"
TOTAL_PAGES = 3  

def scroll_infotec(driver):
    """
    Scroll para activar Lazy Load de imágenes (data-src).
    """
    print("   [Infotec] Bajando para cargar imágenes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1) 
        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

def extract_page_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []


    cards = soup.select('article.product-miniature')

    for card in cards:
        try:

            name_tag = card.select_one('.product-title a')
            if not name_tag: continue
            name = name_tag.get_text(strip=True)


            price_tag = card.select_one('.product-price')
            price = 0.0
            if price_tag:
                raw_text = price_tag.get_text(strip=True)

                clean_text = re.sub(r'[^\d.]', '', raw_text.replace(",", ""))
                try: price = float(clean_text)
                except: price = 0.0



            img_tag = card.select_one('img.product-thumbnail-first')
            image_url = None
            
            if img_tag:
                if img_tag.get('data-src'):
                    image_url = img_tag.get('data-src')
                elif img_tag.get('src'):
                    image_url = img_tag.get('src')
            

            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url



            pid = card.get('data-id-product')
            if not pid:
                pid = name.replace(" ", "-").replace("/", "").upper()[:20]


            store = "Infotec"

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": store
                })

        except Exception:
            continue
            
    return page_products

def scrape(driver):
    
    all_products = []
    print(f"--- Scrapeando INFOTEC ({BASE_URL}) ---")

    for page in range(1, TOTAL_PAGES + 1):
        target_url = f"{BASE_URL}?page={page}"
        print(f"   [Infotec] Procesando Página {page}/{TOTAL_PAGES}...")
        
        try:
            driver.get(target_url)
            
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product-miniature"))
                )
            except TimeoutException:
                print(f"   [Infotec] Timeout en p.{page}. Intentando igual...")

            scroll_infotec(driver)
            
            products = extract_page_data(driver.page_source)
            print(f"   [Infotec] Encontrados: {len(products)}")
            all_products.extend(products)
            
            time.sleep(2) 

        except Exception as e:
            print(f"   [Infotec] Error en página {page}: {e}")

    return all_products