
import sys
import utils

from sites import lenovo 


def main():
    driver = None
    try:
        print("INICIANDO SCRAPER DESDE MAIN")
        driver = utils.get_driver()


        try:
            data_lenovo = lenovo.scrape(driver)
            utils.send_to_api(data_lenovo, "Lenovo")
        except Exception as e:
            print(f" Error en Lenovo: {e}")

    except Exception as e:
        print(f"Error Fatal en Main: {e}")
    finally:
        if driver:
            print("Cerrando navegador...")
            driver.quit()

if __name__ == "__main__":
    main()