import time
import json
import random
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

def setup_driver():
    chrome_options = Options()
    

    chrome_options.add_argument("--headless=new") 
    

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    


    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    

    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    


    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver
def scroll_memorykings(driver):
    print("   [MK] Bajando para cargar catálogo...")

    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 700);")
        time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def extract_category_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_products = []
    base_url = "https://www.memorykings.pe"


    content_divs = soup.select('div.content')

    for content in content_divs:
        try:
            item = {}
            

            link_tag = content.find_parent('a')
            if not link_tag: continue


            title_tag = content.select_one('.title h4')
            item['name'] = title_tag.get_text(strip=True) if title_tag else "Sin Nombre"



            price_div = content.select_one('.price')
            if not price_div:
                price_div = content.select_one('.price-before') 
            
            price_text = "Agotado"
            if price_div:
                raw_text = price_div.get_text(strip=True)

                match = re.search(r'S/\s*([\d,]+\.?\d*)', raw_text)
                if match:
                    price_text = "S/ " + match.group(1)
                else:

                    price_text = raw_text
            
            item['price'] = price_text




            img_tag = link_tag.select_one('.image img')
            img_url = "No imagen"
            if img_tag:
                src = img_tag.get('src') or img_tag.get('data-src')
                if src:

                    if not src.startswith('http'):
                        img_url = base_url + src if src.startswith('/') else base_url + '/' + src
                    else:
                        img_url = src
            item['image_url'] = img_url


            href = link_tag.get('href')
            if href:
                item['url'] = base_url + href if not href.startswith('http') else href
            else:
                item['url'] = ""


            stock_tag = content.select_one('.stock b')
            item['stock'] = stock_tag.get_text(strip=True) if stock_tag else "?"
            
            code_tag = content.select_one('.code b')
            item['sku'] = code_tag.get_text(strip=True) if code_tag else "N/A"

            page_products.append(item)

        except Exception:
            continue
            
    return page_products

def main():

    categories = [
        "https://www.memorykings.pe/listados/247/laptops-intel-core-i3",
        "https://www.memorykings.pe/listados/258/laptops-intel-core-i5",
        "https://www.memorykings.pe/listados/257/laptops-intel-core-i7",
        "https://www.memorykings.pe/listados/464/laptops-intel-core-ultra-5",
        "https://www.memorykings.pe/listados/927/laptops-intel-core-i9",
        "https://www.memorykings.pe/listados/465/laptops-intel-core-ultra-7",
        "https://www.memorykings.pe/listados/1263/laptops-intel-core-ultra-9"
    ]
    
    all_products = []
    driver = None

    try:
        print("--- Iniciando Memory Kings ---")
        driver = setup_driver()

        for url in categories:
            cat_name = url.split('/')[-1]
            print(f"\n[MK] Procesando: {cat_name}")
            
            try:
                driver.get(url)
                

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "content"))
                    )
                except:
                    print("   -> Alerta: Timeout (posible categoría vacía).")

                scroll_memorykings(driver)
                
                data = extract_category_data(driver.page_source)
                print(f"   -> Encontrados: {len(data)}")
                all_products.extend(data)
                
                time.sleep(3)

            except Exception as e:
                print(f"   -> Error procesando categoría: {e}")


        with open('memorykings_laptops.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=4, ensure_ascii=False)
        print(f"Total Final: {len(all_products)} guardados.")

    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()