# scraper/sites/hp.py
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.hp.com/pe-es/shop/laptops.html"
TOTAL_PAGES = 4 # Configuración de cuántas páginas leer

def scroll_para_imagenes(driver):
    """
    Hace scroll progresivo para activar el Lazy Loading de HP.
    Tu lógica original conservada.
    """
    print("   [HP] Cargando imágenes (scroll)...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Bajamos en pasos para dar tiempo a que las imágenes aparezcan
    for pos in range(0, last_height, 700):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
    
    # Scroll final al fondo
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def extract_page_data(html_content):
    """Parsea el HTML de una página específica."""
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []

    cards = soup.select('li.product-item')
    
    for card in cards:
        try:
            # 1. NOMBRE
            name_tag = card.select_one('a.product-item-link')
            if not name_tag: continue
            name = name_tag.get_text(strip=True)
            
            # 2. PRECIO
            # Buscamos precio final o el genérico
            price_tag = card.select_one('[data-price-type="finalPrice"] .price') or card.select_one('.price-box .price')
            
            if not price_tag: continue
            
            # Limpieza de precio para la API (S/. 4,500.00 -> 4500.0)
            raw_text = price_tag.get_text(strip=True)
            # Elimina todo lo que no sea dígito o punto (cuidado con los miles en ES)
            # Asumimos formato S/. 1,234.00 -> quitamos comas
            clean_text = re.sub(r'[^\d,.]', '', raw_text).replace(",", "")
            try:
                price = float(clean_text)
            except:
                price = 0.0

            # 3. IMAGEN
            img_tag = card.select_one('img.product-image-photo')
            image_url = None
            
            if img_tag:
                src = img_tag.get('src')
                if src and "placeholder" not in src and "lazy" not in src:
                    image_url = src
                elif img_tag.get('data-src'):
                    image_url = img_tag.get('data-src')
                elif img_tag.get('data-original'):
                    image_url = img_tag.get('data-original')

            # 4. ID (SKU)
            # HP suele poner el ID en un atributo data-product-id o similar, 
            # pero por seguridad generamos uno basado en el nombre si falla.
            pid = name.replace(" ", "-").replace("/", "").upper()[:20]
            
            # URL del producto (Opcional, pero útil si quisieras guardarlo)
            product_url = name_tag.get('href')

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": "HP" # Etiqueta importante para el Dashboard
                })

        except Exception as e:
            continue
            
    return page_products

def scrape(driver):
    """Función principal llamada por el orquestador main.py"""
    all_products = []
    
    print(f"--- Scrapeando HP ({BASE_URL}) ---")

    for page in range(1, TOTAL_PAGES + 1):
        target_url = f"{BASE_URL}?p={page}"
        print(f"   [HP] Procesando Página {page}/{TOTAL_PAGES}...")
        
        try:
            driver.get(target_url)
            
            # Esperar carga de la rejilla
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".product-items"))
                )
            except TimeoutException:
                print(f"   [HP] Timeout en p.{page}. Intentando parsear igual...")

            # Scroll para imágenes
            scroll_para_imagenes(driver)
            
            # Extraer
            current_products = extract_page_data(driver.page_source)
            print(f"   [HP] Encontrados en p.{page}: {len(current_products)}")
            
            all_products.extend(current_products)
            
        except Exception as e:
            print(f"   [HP] Error en página {page}: {e}")

    return all_products