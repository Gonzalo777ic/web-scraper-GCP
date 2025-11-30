
import time
import random
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

URLS = [
        "https://www.amazon.com/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&language=es&ref=lp_565108_sar",
        "https://www.amazon.com/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=2&language=es&qid=1764484056&xpid=KnbWhSpQY3doM&ref=sr_pg_2",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=3&language=es&qid=1764484803&xpid=KnbWhSpQY3doM&ref=sr_pg_3",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=4&language=es&qid=1764485164&xpid=YFF_xqLNeb_f6&ref=sr_pg_4",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=5&language=es&qid=1764485172&xpid=YFF_xqLNeb_f6&ref=sr_pg_5",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=6&language=es&qid=1764485180&xpid=YFF_xqLNeb_f6&ref=sr_pg_6",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=7&language=es&qid=1764485224&xpid=YFF_xqLNeb_f6&ref=sr_pg_7",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=8&language=es&qid=1764485233&xpid=YFF_xqLNeb_f6&ref=sr_pg_8",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=9&language=es&qid=1764485240&xpid=YFF_xqLNeb_f6&ref=sr_pg_9",
        "https://www.amazon.com/-/es/s?i=computers&rh=n%3A565108&s=popularity-rank&fs=true&page=10&language=es&qid=1764485248&xpid=YFF_xqLNeb_f6&ref=sr_pg_10"
    ]

def scroll_humano(driver):
    
    print("   [Amazon] Bajando para cargar imágenes...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    current_pos = 0
    while current_pos < last_height:
        step = random.randint(600, 1000)
        current_pos += step
        driver.execute_script(f"window.scrollTo(0, {current_pos});")
        time.sleep(random.uniform(0.1, 0.3))
        if current_pos > last_height * 0.9: break
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

def extract_page_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []


    if "Enter the characters you see below" in soup.get_text():
        print("   [Amazon] ⚠️ ALERTA: CAPTCHA DETECTADO.")
        return []


    cards = soup.select('div[data-component-type="s-search-result"]')
    if not cards: cards = soup.select('.s-result-item')

    for card in cards:
        try:

            title_tag = card.select_one('h2 span')
            if not title_tag: continue
            name = title_tag.get_text(strip=True)


            price_tag = card.select_one('.a-price .a-offscreen') or card.select_one('.a-color-price')
            price = 0.0
            if price_tag:
                raw_text = price_tag.get_text(strip=True)


                clean_text = re.sub(r'[^\d.]', '', raw_text)
                try: price = float(clean_text)
                except: price = 0.0


            img_tag = card.select_one('img.s-image')
            image_url = None
            if img_tag:
                image_url = img_tag.get('src')
            


            pid = card.get("data-asin")
            if not pid: 
                pid = re.sub(r'\W+', '', name)[:15].upper()

            if price > 0:
                page_products.append({
                    "product_id": pid,
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "currency": "USD", 
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "store": "Amazon"
                })
        except: continue
        
    return page_products

def scrape(driver):
    
    all_products = []
    print(f"--- Scrapeando AMAZON ({len(URLS)} páginas) ---")

    for i, url in enumerate(URLS):
        print(f"   [Amazon] Procesando Página {i+1}...")
        try:
            driver.get(url)
            time.sleep(random.uniform(2, 4)) 


            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
                )
            except TimeoutException:
                pass 

            scroll_humano(driver)
            
            products = extract_page_data(driver.page_source)
            print(f"   [Amazon] Encontrados: {len(products)}")
            all_products.extend(products)


            if i < len(URLS) - 1:
                time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"   [Amazon] Error en página {i+1}: {e}")

    return all_products