import requests
import time
import random
import os
API_HOST = os.getenv("API_HOST", "http://localhost")
API_PORT = os.getenv("API_PORT", "80")
API_URL = f"{API_HOST}:{API_PORT}/prices"
def scrape_product(product_name, product_id):
    
    print(f"[{time.strftime('%H:%M:%S')}] Scraping: {product_name}...")
    price = round(random.uniform(900.0, 1500.0), 2)
    data = {
        "product_id": product_id,
        "price": price,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return data

def run_scraper():
    
    products_to_track = [
        ("Laptop X Pro", "LAPTOP-XP-2024"),
        ("Monitor 4K Z", "MONITOR-4K-001"),
        ("Teclado Mecánico", "KEYBOARD-MECH-G9")
    ]
    
    for name, pid in products_to_track:
        scraped_data = scrape_product(name, pid)
        try:
            print(f"Enviando datos de {name} a: {API_URL}")
            response = requests.post(API_URL, json=scraped_data, timeout=5)
            
            if response.status_code == 200:
                print(f"Datos de {pid} enviados correctamente. Precio: {scraped_data['price']}")
            else:
                print(f"Error al enviar datos: Status {response.status_code}, {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"!!! Error de Conexión: No se pudo conectar a la API en {API_URL}. ¿Está el servicio 'api-service' corriendo?")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    print("--- Iniciando Microservicio Scraper ---")
    run_scraper()
    print("--- Ejecución del Scraper terminada ---")