
import time
import re
import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.memorykings.pe"

CATEGORIES = [
    "https://www.memorykings.pe/listados/247/laptops-intel-core-i3", 
    "https://www.memorykings.pe/listados/258/laptops-intel-core-i5",
    "https://www.memorykings.pe/listados/257/laptops-intel-core-i7",
    "https://www.memorykings.pe/listados/464/laptops-intel-core-ultra-5",
    "https://www.memorykings.pe/listados/927/laptops-intel-core-i9"
]

def scroll_memorykings(driver):
    
    print("   [Memory Kings] Bajando para cargar catálogo...")

    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 700);")
        time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def extract_category_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []
    


    items = soup.select('li div a')
    
    for item_link in items:
        try:
            content_div = item_link.select_one('.content')
            if not content_div: continue


            title_tag = content_div.select_one('.title h4')
            if not title_tag: continue
            name = title_tag.get_text(strip=True)


            price = 0.0
            price_div = content_div.select_one('.price')
            if not price_div:
                price_div = content_div.select_one('.price-before') 
            
            if price_div:
                raw_text = price_div.get_text(strip=True)


                match = re.search(r'S/\s*([\d,]+\.?\d*)', raw_text)
                if match:

                    clean_str = match.group(1).replace(",", "")
                    try: price = float(clean_str)
                    except: price = 0.0
            


            img_div = item_link.select_one('.image img')
            image_url = None
            
            if img_div:
                src = img_div.get('src') or img_div.get('data-src')
                if src:
                    if not src.startswith('http'):
                        image_url = BASE_URL + src if src.startswith('/') else BASE_URL + '/' + src
                    else:
                        image_url = src


            pid = ""
            code_tag = content_div.select_one('.code') 
            if code_tag:

                pid = code_tag.get_text(strip=True).replace("Código interno:", "").strip()
            
            if not pid:
                pid = name.replace(" ", "-").upper()[:20]

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": "Memory Kings"
                })

        except Exception:
            continue
            
    return page_products

def scrape(driver):
    
    all_products = []
    print(f"--- Scrapeando MEMORY KINGS ({len(CATEGORIES)} categorías) ---")

    for url in CATEGORIES:
        cat_name = url.split('/')[-1]
        print(f"   [Memory Kings] Procesando: {cat_name}...")
        
        try:
            driver.get(url)
            

            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "content"))
                )
            except TimeoutException:
                print(f"   [Memory Kings] Timeout en {cat_name}. Intentando extraer igual...")

            scroll_memorykings(driver)
            
            current_products = extract_category_data(driver.page_source)
            print(f"   [Memory Kings] Encontrados: {len(current_products)}")
            
            all_products.extend(current_products)
            time.sleep(3) 

        except Exception as e:
            print(f"   [Memory Kings] Error en {cat_name}: {e}")

    return all_products