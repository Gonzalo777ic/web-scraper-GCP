# scraper/sites/realplaza.py
import time
import re
import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.realplaza.com/computacion/laptops"
TOTAL_PAGES = 10 

def scroll_realplaza(driver):
    """Scroll para renderizar componentes React de VTEX IO."""
    print("   [Real Plaza] Bajando para renderizar componentes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    step = 500
    for pos in range(0, last_height, step):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.15)
        if pos % 2000 == 0:
            last_height = driver.execute_script("return document.body.scrollHeight")
            
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    driver.execute_script("window.scrollBy(0, -500);")
    time.sleep(1)

def extract_page_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []

    cards = soup.select('.vtex-product-summary-2-x-container')
    if not cards:
        cards = soup.select('.vtex-search-result-3-x-galleryItem')

    for card in cards:
        try:
            # 1. NOMBRE
            name_tag = card.select_one('.vtex-product-summary-2-x-productBrand')
            if not name_tag: continue
            name = name_tag.get_text(strip=True)

            # 2. PRECIO
            price = 0.0
            oh_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__ThirdPrice span')
            online_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__OfferPrice span')
            regular_price = card.select_one('.realplaza-product-custom-0-x-productSummaryPrice__Option__RegularPrice span')
            generic_price = card.select_one('.vtex-product-summary-2-x-sellingPrice')

            raw_text = ""
            if oh_price: raw_text = oh_price.get_text(strip=True)
            elif online_price: raw_text = online_price.get_text(strip=True)
            elif regular_price: raw_text = regular_price.get_text(strip=True)
            elif generic_price: raw_text = generic_price.get_text(strip=True)

            if raw_text and "Agotado" not in raw_text:
                clean_text = re.sub(r'[^\d.]', '', raw_text.replace(",", ""))
                try: price = float(clean_text)
                except: price = 0.0

            # 3. IMAGEN
            img_tag = card.select_one('img.vtex-product-summary-2-x-imageNormal')
            image_url = None
            if img_tag:
                image_url = img_tag.get('src')

            # 4. ID
            link_tag = card.select_one('a.vtex-product-summary-2-x-clearLink')
            pid = ""
            if link_tag:
                href = link_tag.get('href')
                if href:
                    pid = href.strip("/").split("/")[-1][:20].upper()
            
            if not pid:
                pid = name.replace(" ", "-").upper()[:20]

            # 5. VENDEDOR
            seller_tag = card.select_one('.realplaza-product-custom-0-x-sellerNameParagraph')
            seller = seller_tag.get_text(strip=True) if seller_tag else "Real Plaza"

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "PEN",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": f"Real Plaza ({seller})"
                })

        except Exception:
            continue
            
    return page_products

def scrape(driver):
    all_products = []
    print(f"--- Scrapeando REAL PLAZA ({BASE_URL}) ---")

    for page in range(1, TOTAL_PAGES + 1):
        target_url = f"{BASE_URL}?page={page}"
        print(f"   [Real Plaza] Procesando Página {page}/{TOTAL_PAGES}...")
        
        try:
            driver.get(target_url)
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "vtex-product-summary-2-x-container"))
                )
            except TimeoutException:
                print(f"   [Real Plaza] Timeout en p.{page}. Intentando igual...")

            scroll_realplaza(driver)
            products = extract_page_data(driver.page_source)
            print(f"   [Real Plaza] Encontrados: {len(products)}")
            all_products.extend(products)
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"   [Real Plaza] Error en página {page}: {e}")

    return all_products