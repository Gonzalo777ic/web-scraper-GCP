
import os
import requests
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType


API_HOST = os.getenv("API_HOST", "http://api-service")
API_PORT = os.getenv("API_PORT", "80")
API_URL = f"{API_HOST}:{API_PORT}/prices"

def get_driver():
    
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    return webdriver.Chrome(service=service, options=opts)

def send_to_api(data_list, store_name):
    
    print(f"[{store_name}] Enviando {len(data_list)} productos...")
    success_count = 0
    for p in data_list:
        try:

            if "image_url" not in p: p["image_url"] = None
            
            res = requests.post(API_URL, json=p, timeout=5)
            if res.status_code == 200: success_count += 1
        except Exception as e:
            print(f"Error enviando {p.get('product_id')}: {e}")
    print(f"[{store_name}] Finalizado. Éxito: {success_count}/{len(data_list)}")