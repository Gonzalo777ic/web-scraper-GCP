import time
import json
import sys
import os
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN API ---
API_HOST = os.getenv("API_HOST", "http://api-service")
API_PORT = os.getenv("API_PORT", "80")
API_URL = f"{API_HOST}:{API_PORT}/prices"

def setup_driver():
    """Configura Chrome Headless para Docker/GKE."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    try:
        # Instala automáticamente el driver compatible con el Chrome instalado en el Dockerfile
        service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error inicializando driver: {e}")
        sys.exit(1)

def scroll_inteligente(driver):
    """Baja buscando el botón 'Ver más'."""
    print("Iniciando scroll inteligente...")
    consecutive_scrolls_without_button = 0

    while True:
        boton_encontrado = False
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(@class, 'pc_more') or contains(., 'Ver más')]")
            if btn.is_displayed():
                print("   [JS] Botón 'Ver más' encontrado. Click.")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(4) 
                consecutive_scrolls_without_button = 0
                boton_encontrado = True
        except NoSuchElementException:
            pass
        except Exception:
            pass

        if not boton_encontrado:
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.5)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            current_pos = driver.execute_script("return window.pageYOffset + window.innerHeight")
            
            if current_pos >= new_height - 200:
                consecutive_scrolls_without_button += 1
                if consecutive_scrolls_without_button >= 2: # Limitamos a 2 intentos para no eternizar
                    print("   [JS] Fin del scroll.")
                    break
                driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(1)
            else:
                consecutive_scrolls_without_button = 0

def extract_and_send(html_content):
    """Analiza con BS4 y envía a la API."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Buscamos por la clase LI o DIV
    cards = soup.find_all("li", class_="product_item")
    if not cards:
        cards = soup.find_all("div", class_="dlp-product-card")

    print(f"Parsing: Se encontraron {len(cards)} tarjetas.")

    for i, card in enumerate(cards):
        try:
            # Título
            title_tag = card.select_one('.product_title a') or card.select_one('a.lazy_href')
            name = title_tag.get_text(strip=True) if title_tag else "Sin Nombre"
            
            # Precio
            price_tag = card.select_one('.price-summary-info .price-title') or card.select_one('.price-title')
            
            if price_tag:
                raw_text = price_tag.get_text(strip=True)
                # Limpieza: "S/. 2,199" -> 2199.0
                clean_text = re.sub(r'[^\d,]', '', raw_text).replace(",", "")
                try:
                    price = float(clean_text)
                except:
                    price = 0.0
            else:
                price = 0.0

            if price > 0:
                # Generar ID
                product_id = card.get("data-product-code")
                if not product_id:
                    product_id = re.sub(r'\W+', '', name)[:20].upper()

                payload = {
                    "product_id": product_id,
                    "price": price,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "name": name,
                    "currency": "PEN"
                }

                # ENVIAR A LA API
                print(f"   + Enviando [{product_id}] S/{price}...", end="")
                try:
                    res = requests.post(API_URL, json=payload, timeout=5)
                    if res.status_code == 200:
                        print(" OK")
                    else:
                        print(f" Error {res.status_code}")
                except Exception as e:
                    print(f" Fallo red: {e}")

        except Exception as e:
            continue

def main():
    url = "https://www.lenovo.com/pe/es/d/ofertas/intel/"
    driver = None
    try:
        print("--- Iniciando Selenium en GKE ---")
        driver = setup_driver()
        print(f"Navegando a: {url}")
        driver.get(url)
        
        # Espera carga inicial
        time.sleep(5)

        # Ejecutar Scroll
        scroll_inteligente(driver)
        
        # Extraer y Enviar
        print("Procesando HTML final...")
        extract_and_send(driver.page_source)
        
    except Exception as e:
        print(f"ERROR FATAL: {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
