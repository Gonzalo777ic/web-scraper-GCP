import sys
import utils
import time


from sites import lenovo
from sites import hp
from sites import amazon
from sites import asus
from sites import falabella
from sites import infotec
from sites import oechsle
from sites import realplaza






def main():
    print("INICIANDO SCRAPERS")


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
            

            driver = utils.get_driver()
            

            data = modulo.scrape(driver)
            

            if data:
                utils.send_to_api(data, nombre)
            else:
                print(f"{nombre} no devolvió datos (0 encontrados).")

        except Exception as e:
            print(f"Error CRÍTICO en {nombre}: {e}")
        
        finally:

            if driver:
                print(f"--- Cerrando navegador de {nombre} ---")
                try:
                    driver.quit()
                except:
                    pass

            time.sleep(2)

    print("\nProceso Global Finalizado.")

if __name__ == "__main__":
    main()
