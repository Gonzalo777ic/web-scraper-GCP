# scraper/sites/falabella.py
import time
import re
import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.falabella.com.pe/falabella-pe/category/cat40712/Laptops"
TOTAL_PAGES = 11

def scroll_falabella(driver):
    """Scroll para cargar imágenes lazy."""
    print("   [Falabella] Bajando para cargar imágenes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 500
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.15)
        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")
            
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_page_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []

    cards = soup.find_all('div', attrs={"data-testid": "ssr-pod"})
    if not cards:
        cards = soup.find_all('div', id=re.compile(r'^testId-pod-\d+'))

    for card in cards:
        try:
            # 1. NOMBRE
            name_tag = card.find('b', id=re.compile(r'^testId-pod-displaySubTitle'))
            if not name_tag: name_tag = card.find('b', class_=re.compile('pod-subTitle'))
            name = name_tag.get_text(strip=True) if name_tag else "Sin Nombre"

            # 2. PRECIO (Prioridad: CMR > Internet > Normal)
            price = 0.0
            price_section = card.find('div', id=re.compile(r'^testId-pod-prices'))
            
            if price_section:
                # Intentar sacar precio limpio de los atributos data (es más seguro)
                li_cmr = price_section.find('li', attrs={"data-cmr-price": True})
                li_internet = price_section.find('li', attrs={"data-internet-price": True})
                li_normal = price_section.find('li', attrs={"data-normal-price": True})
                
                raw_price = ""
                if li_cmr: raw_price = li_cmr['data-cmr-price']
                elif li_internet: raw_price = li_internet['data-internet-price']
                elif li_normal: raw_price = li_normal['data-normal-price']
                else:
                    # Fallback visual
                    prices = price_section.find_all('span')
                    for p in prices:
                        txt = p.get_text(strip=True)
                        if "S/" in txt:
                            raw_price = txt
                            break
                
                # Limpieza: eliminar todo menos números y punto
                clean_text = re.sub(r'[^\d.]', '', raw_price.replace(",", ""))
                try: price = float(clean_text)
                except: price = 0.0

            # 3. IMAGEN
            img_tag = card.find('img', id=re.compile(r'^testId-pod-image'))
            image_url = None
            if img_tag:
                src = img_tag.get('src')
                if src:
                    image_url = src
                    if image_url.startswith("//"): image_url = "https:" + image_url

            # 4. ID
            # Falabella suele tener el ID en el atributo ID del div principal
            # ej: testId-pod-12345678. Extraemos el número.
            card_id = card.get("id")
            pid = ""
            if card_id:
                match = re.search(r'\d+', card_id)
                if match: pid = match.group()
            
            if not pid: pid = name.replace(" ", "-").upper()[:20]

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": "Falabella"
                })

        except Exception:
            continue
            
    return page_products

def scrape(driver):
    """Función principal para main.py"""
    all_products = []
    print(f"--- Scrapeando FALABELLA ({BASE_URL}) ---")

    for page in range(1, TOTAL_PAGES + 1):
        target_url = f"{BASE_URL}?page={page}"
        print(f"   [Falabella] Procesando Página {page}/{TOTAL_PAGES}...")
        
        try:
            driver.get(target_url)
            
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='ssr-pod']"))
                )
            except TimeoutException:
                print(f"   [Falabella] Timeout en p.{page}. Intentando igual...")

            scroll_falabella(driver)
            
            products = extract_page_data(driver.page_source)
            print(f"   [Falabella] Encontrados: {len(products)}")
            all_products.extend(products)
            
            time.sleep(random.uniform(2, 4)) # Pausa antibloqueo

        except Exception as e:
            print(f"   [Falabella] Error en página {page}: {e}")

    return all_products