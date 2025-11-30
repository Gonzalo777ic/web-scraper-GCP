import requests
import json
from google.cloud import bigquery
import os
import time

# Configuración
API_URL = "http://api-service/prices" # URL interna del cluster
DATASET_ID = "price_monitor_dw"
TABLE_ID = "daily_snapshot"
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

def run_etl():
    print("Iniciando ETL: API -> BigQuery...")
    
    # 1. EXTRACT (Desde tu API interna)
    try:
        print("   [Extract] Descargando datos de la API...")
        res = requests.get(API_URL)
        data = res.json()
        print(f"   -> {len(data)} registros extraídos.")
    except Exception as e:
        print(f"Error extrayendo datos: {e}")
        return

    if not data:
        print("No hay datos para cargar.")
        return

    # 2. TRANSFORM (Adaptar para BigQuery)
    rows_to_insert = []
    for item in data:
        # Solo seleccionamos los campos que definimos en el esquema de BigQuery
        rows_to_insert.append({
            "product_id": item.get("product_id"),
            "price": item.get("price"),
            "store": item.get("store"),
            "timestamp": item.get("timestamp")
        })

    # 3. LOAD (Subir a BigQuery)
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        
        print(f"   [Load] Insertando en {table_ref}...")
        errors = client.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            print(f"Errores al insertar: {errors}")
        else:
            print(f"Éxito: {len(rows_to_insert)} filas cargadas en BigQuery.")
            
    except Exception as e:
        print(f"Error cargando a BigQuery: {e}")

if __name__ == "__main__":
    run_etl()
