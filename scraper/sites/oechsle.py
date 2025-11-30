# scraper/sites/oechsle.py
import time
import re
import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.oechsle.pe/tecnologia/computo/laptops"
QUERY_PARAMS = "fq=C%3A%2F160%2F168%2F209%2F"
TOTAL_PAGES = 11

def scroll_oechsle(driver):
    """Scroll suave para Oechsle (VTEX)."""
    print("   [Oechsle] Bajando para cargar imágenes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_page_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []

    cards = soup.select('div.resultItem')

    for card in cards:
        try:
            # 1. NOMBRE
            name = card.get('data-product-name')
            if not name:
                name_tag = card.select_one('.resultItem__detail--name')
                if name_tag: name = name_tag.get_text(strip=True)
            if not name: continue

            # 2. PRECIO
            price = 0.0
            price_container = card.select_one('.resultItem__detail--price')
            
            if price_container:
                # Prioridad: Precio Normal > Precio Oh!
                # (Para la API necesitamos un solo float, usamos el estándar o el mejor disponible)
                standard_price = price_container.select_one('.price:not(.priceList):not(.priceTOh) .value')
                oh_price = price_container.select_one('.priceTOh .value')
                
                raw_text = ""
                if standard_price: raw_text = standard_price.get_text(strip=True)
                elif oh_price: raw_text = oh_price.get_text(strip=True)
                else:
                    # Fallback Regex
                    all_text = price_container.get_text()
                    match = re.search(r'S/\s*[\d,.]+', all_text)
                    if match: raw_text = match.group(0)

                # Limpieza: "S/. 3,999.00" -> 3999.0
                if raw_text:
                    clean_text = re.sub(r'[^\d.]', '', raw_text.replace(",", ""))
                    try: price = float(clean_text)
                    except: price = 0.0

            # 3. IMAGEN
            img_tag = card.select_one('img.resultItem__image')
            image_url = None
            if img_tag:
                src = img_tag.get('src')
                if src:
                    image_url = src
                    # Si src parece placeholder, usar data-src
                    if "arquivos/ids" not in src and img_tag.get('data-src'):
                        image_url = img_tag.get('data-src')

            # 4. ID
            # Oechsle suele tener data-product-id
            pid = card.get('data-product-id')
            if not pid:
                pid = name.replace(" ", "-").replace("/", "").upper()[:20]

            # 5. VENDEDOR (Extra)
            seller_tag = card.select_one('.resultItem__by-seller')
            seller = seller_tag.get_text(strip=True) if seller_tag else "Oechsle"

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": f"Oechsle ({seller})" # Incluimos el vendedor real
                })

        except Exception:
            continue
            
    return page_products

def scrape(driver):
    """Función principal para main.py"""
    all_products = []
    print(f"--- Scrapeando OECHSLE ({BASE_URL}) ---")

    for page in range(1, TOTAL_PAGES + 1):
        target_url = f"{BASE_URL}?{QUERY_PARAMS}&page={page}"
        print(f"   [Oechsle] Procesando Página {page}/{TOTAL_PAGES}...")
        
        try:
            driver.get(target_url)
            
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "resultItem"))
                )
            except TimeoutException:
                print(f"   [Oechsle] Timeout en p.{page}. Intentando igual...")

            scroll_oechsle(driver)
            
            products = extract_page_data(driver.page_source)
            print(f"   [Oechsle] Encontrados: {len(products)}")
            all_products.extend(products)
            
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"   [Oechsle] Error en página {page}: {e}")

    return all_products