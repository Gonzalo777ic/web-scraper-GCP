import sys
import utils
import time

# Importamos las tiendas
from sites import lenovo
from sites import hp
from sites import amazon
from sites import asus
from sites import falabella
from sites import infotec
from sites import oechsle
from sites import realplaza

# Tiendas omitidas por WAF (pero importadas para referencia futura)
# from sites import magitech
# from sites import memorykings
# from sites import supertec

def main():
    print("INICIANDO SCRAPERS")

    # Lista de tiendas activas
    tiendas_activas = [
        (lenovo, "Lenovo"),
        (hp, "HP"),
        (asus, "Asus"),
        (falabella, "Falabella"),
        (infotec, "Infotec"),
        (oechsle, "Oechsle"),
        (realplaza, "Real Plaza"),
        (amazon, "Amazon")
    ]

    print(f"Procesando {len(tiendas_activas)} tiendas secuencialmente.")

    for modulo, nombre in tiendas_activas:
        driver = None
        try:
            print(f"\n==========================================")
            print(f"--- Iniciando Turno de: {nombre} ---")
            
            # 1. ABRIR NAVEGADOR FRESCO (Limpia RAM)
            driver = utils.get_driver()
            
            # 2. EJECUTAR SCRAPER
            data = modulo.scrape(driver)
            
            # 3. ENVIAR DATOS
            if data:
                utils.send_to_api(data, nombre)
            else:
                print(f"{nombre} no devolvió datos (0 encontrados).")

        except Exception as e:
            print(f"Error CRÍTICO en {nombre}: {e}")
        
        finally:
            # 4. CERRAR NAVEGADOR INMEDIATAMENTE (Liberar RAM)
            if driver:
                print(f"--- Cerrando navegador de {nombre} ---")
                try:
                    driver.quit()
                except:
                    pass
            # Pequeña pausa para que el sistema operativo recupere recursos
            time.sleep(2)

    print("\nProceso Global Finalizado.")

if __name__ == "__main__":
    main()
