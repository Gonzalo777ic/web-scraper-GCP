# scraper/sites/supertec.py
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

BASE_URL = "https://supertec.com.pe/productos-categorias/1/PORTATILES"
BASE_DOMAIN = "https://supertec.com.pe/"

def scroll_supertec(driver):
    """Scroll para cargar imágenes."""
    print("   [Supertec] Bajando para cargar catálogo...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 400
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

def extract_products(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []

    # Selector principal
    cards = soup.select('a.prods')

    for card in cards:
        try:
            # 1. URL y FILTRADO
            href = card.get('href')
            if not href: continue
            
            product_url = href if href.startswith('http') else BASE_DOMAIN + href.lstrip('/')
            
            # FILTRO ANTI-BASURA
            if "productos-por-marcas" in product_url:
                continue

            # 2. NOMBRE
            name_tag = card.select_one('.nproducts')
            if not name_tag: continue
            name = name_tag.get_text(strip=True)

            # 3. PRECIO
            price = 0.0
            price_tag = card.select_one('.precioactual')
            if price_tag:
                raw_text = price_tag.get_text(strip=True)
                # Supertec a veces pone "S/. 3000 | $ 800". Nos quedamos con la parte de S/.
                # Buscamos explícitamente el lado que tenga S/. o asumimos el primero
                parts = raw_text.split('|')
                soles_part = parts[0]
                for part in parts:
                    if "S/." in part:
                        soles_part = part
                        break
                
                clean_text = re.sub(r'[^\d.]', '', soles_part.replace(",", ""))
                try: price = float(clean_text)
                except: price = 0.0

            # 4. IMAGEN
            img_tag = card.select_one('img.img80')
            image_url = None
            if img_tag:
                src = img_tag.get('src')
                if src:
                    if not src.startswith('http'):
                        image_url = BASE_DOMAIN + src.lstrip('/')
                    else:
                        image_url = src

            # 5. ID (SKU)
            pid = product_url.split('/')[-1][:20].upper()
            if not pid or len(pid) < 5:
                pid = name.replace(" ", "-").upper()[:20]

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": "Supertec"
                })

        except Exception:
            continue
            
    return page_products

def scrape(driver):
    """Función principal para main.py"""
    all_products = []
    print(f"--- Scrapeando SUPERTEC ({BASE_URL}) ---")

    try:
        driver.get(BASE_URL)
        
        # Espera inicial
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "prods"))
            )
        except TimeoutException:
            print("   [Supertec] Timeout inicial.")

        # --- PÁGINA 1 ---
        print("   [Supertec] Procesando Página 1...")
        scroll_supertec(driver)
        products_p1 = extract_products(driver.page_source)
        print(f"   [Supertec] P1 Encontrados: {len(products_p1)}")
        all_products.extend(products_p1)

        # --- PÁGINA 2 (Navegación AJAX) ---
        try:
            # Buscamos el botón "2" en la paginación usando XPath específico
            next_page_btn = driver.find_element(By.XPATH, "//li[contains(@class, 'paginate')]/a[text()='2']")
            
            if next_page_btn:
                print("   [Supertec] Navegando a Página 2...")
                # Scroll para asegurar que esté en viewport
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_btn)
                time.sleep(1)
                
                # CLICK FUERZADO VIA JS (Soluciona el bloqueo en headless)
                driver.execute_script("arguments[0].click();", next_page_btn)
                
                time.sleep(6) # Espera generosa para carga AJAX
                scroll_supertec(driver)
                
                products_p2 = extract_products(driver.page_source)
                
                # Filtrar duplicados
                existing_ids = set(p['product_id'] for p in all_products)
                new_count = 0
                for p in products_p2:
                    if p['product_id'] not in existing_ids:
                        all_products.append(p)
                        new_count += 1
                
                print(f"   [Supertec] P2 Nuevos agregados: {new_count}")

        except NoSuchElementException:
            print("   [Supertec] No se encontró paginación a la página 2.")
        except Exception as e:
            print(f"   [Supertec] Error cambiando de página: {e}")

    except Exception as e:
        print(f"   [Supertec] Error fatal: {e}")

    return all_products