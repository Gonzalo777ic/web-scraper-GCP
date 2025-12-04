import requests
import json
from google.cloud import bigquery
import os
from datetime import datetime

# Configuración
API_URL = "http://api-service/prices"
DATASET_ID = "price_monitor_dw"
TABLE_ID = "daily_snapshot"
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

def run_etl():
    print("🚀 Iniciando ETL: API -> BigQuery...")
    
    try:
        res = requests.get(API_URL)
        data = res.json()
        print(f"   [Extract] {len(data)} registros extraídos.")
    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")
        return

    if not data:
        print("⚠️ No hay datos para cargar.")
        return

    rows_to_insert = []
    for item in data:
        # --- LÓGICA DE FUERZA DE CAMPO ---
        
        # Leemos el timestamp (que ya sabemos que está bien por el fix anterior)
        ts = item.get("created_at") or item.get("timestamp")
        
        # Aseguramos que los campos de texto no sean None o vacíos
        name = item.get("name") or 'Product Name Missing'
        image = item.get("image_url") or 'No Image URL'
        currency = item.get("currency") or "PEN"


        # Solo cargamos la fila si tenemos un nombre válido y un precio > 0
        if item.get("price") > 0 and name != 'Product Name Missing':
            rows_to_insert.append({
                "product_id": item.get("product_id"),
                "price": item.get("price"),
                "store": item.get("store"),
                "name": name,
                "image_url": image,
                "currency": currency,
                "timestamp": ts 
            })
    
    if not rows_to_insert:
        print("⚠️ No se encontraron filas válidas para insertar.")
        return
        
    # 3. LOAD (Subir a BigQuery)
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        
        print(f"   [Load] Insertando {len(rows_to_insert)} filas en BigQuery...")
        errors = client.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            print(f"❌ Errores al insertar: {errors}")
        else:
            print(f"✅ Éxito: Filas cargadas con name e image.")
            
    except Exception as e:
        print(f"❌ Error cargando a BigQuery: {e}")

if __name__ == "__main__":
    run_etl()
