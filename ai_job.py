import pandas as pd
import numpy as np
import re
import os
from google.cloud import bigquery
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# --- CONFIGURACIÓN ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
# Usamos la tabla diaria para tener más datos de entrenamiento
SOURCE_TABLE = f"{PROJECT_ID}.price_monitor_dw.daily_snapshot"
DEST_TABLE = f"{PROJECT_ID}.price_monitor_dw.ai_market_analysis"

def extract_specs(row):
    """Ingeniería de características avanzada (Tu lógica)"""
    text = str(row['name']).lower()
    
    # --- CPU ---
    cpu_model = re.search(r'(i[3579]-?\d{3,5}h?|ryzen\s?[3579]\s?\d{3,4}h?)', text)
    cpu_model = cpu_model.group(1) if cpu_model else "other"

    if 'i9' in text or 'ryzen 9' in text: cpu_score = 90
    elif 'i7' in text or 'ryzen 7' in text: cpu_score = 70
    elif 'i5' in text or 'ryzen 5' in text: cpu_score = 50
    elif 'i3' in text or 'ryzen 3' in text: cpu_score = 30
    elif 'celeron' in text or 'athlon' in text: cpu_score = 10
    else: cpu_score = 40
    
    # --- RAM ---
    ram = 8
    if re.search(r'32\s*gb', text): ram = 32
    elif re.search(r'16\s*gb', text): ram = 16
    elif re.search(r'12\s*gb', text): ram = 12
    elif re.search(r'4\s*gb', text): ram = 4
    
    # --- STORAGE ---
    storage = 256
    if '2tb' in text: storage = 2000
    elif '1tb' in text: storage = 1000
    elif '512' in text: storage = 512
    elif '256' in text: storage = 256
    elif '128' in text: storage = 128
    elif '64' in text: storage = 64
    
    # --- SCREEN ---
    screen = re.search(r'(\d{2}(\.\d)?)\s*["”]', text)
    screen_inch = float(screen.group(1)) if screen else 15.6
    
    # --- GPU ---
    gpu_model = re.search(r'(rtx\s*\d{3,4}|gtx\s*\d{3,4}|mx\s*\d{3})', text)
    gpu_model = gpu_model.group(1) if gpu_model else "integrated"

    if 'rtx 40' in text: gpu_score = 95
    elif 'rtx 30' in text: gpu_score = 80
    elif 'gtx' in text: gpu_score = 60
    elif 'mx' in text: gpu_score = 30
    else: gpu_score = 0
    
    # --- OTROS ---
    os_windows = 1 if 'windows' in text else 0
    brand = str(row['name']).split()[0].lower()
    is_gaming = int(('gaming' in text) or ('rtx' in text) or ('gtx' in text))
    is_ultrabook = int('ultra' in text or 'slim' in text)
    is_touch = int('touch' in text or '2 en 1' in text or 'convertible' in text)

    return pd.Series([
        brand, cpu_model, gpu_model, cpu_score,
        ram, storage, screen_inch, gpu_score,
        os_windows, is_gaming, is_ultrabook, is_touch
    ])

def run_ai_analysis():
    print("Iniciando Job de IA (XGBoost)...")
    client = bigquery.Client(project=PROJECT_ID)
    
    # 1. DESCARGA DE DATOS (Limpieza en SQL)
    print("   Descargando datos de BigQuery...")
    query = f"""
        SELECT DISTINCT
            product_id,
            name,
            TRIM(SPLIT(store, '(')[OFFSET(0)]) as store_clean,
            store as store_original,
            CASE WHEN currency='USD' THEN price*3.8 ELSE price END AS final_price_pen,
            image_url,
            timestamp
        FROM `{SOURCE_TABLE}`
        WHERE price > 100 AND name IS NOT NULL
    """
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("No hay datos para analizar.")
        return

    print(f"   Procesando {len(df)} registros...")

    # 2. FEATURE ENGINEERING
    # Guardamos store_clean antes de que get_dummies lo borre
    df['tienda_reporte'] = df['store_clean'] 
    
    df[['brand','cpu_model','gpu_model','cpu_score','ram_gb','storage_gb','screen_inch','gpu_score','os_windows','is_gaming','is_ultrabook','is_touch']] = df.apply(extract_specs, axis=1)
    
    # One-Hot Encoding
    df_encoded = pd.get_dummies(df, 
                                columns=['brand','cpu_model','gpu_model','store_clean'], 
                                drop_first=True)
    
    # 3. LIMPIEZA DE OUTLIERS
    df_encoded = df_encoded[df_encoded['final_price_pen'].between(500, 12000)]
    
    # 4. ENTRENAMIENTO
    X = df_encoded.drop(columns=['product_id','name','store_original','final_price_pen','image_url','timestamp', 'tienda_reporte'])
    y = df_encoded['final_price_pen']
    
    print("   Entrenando XGBoost optimizado...")
    model = XGBRegressor(
        n_estimators=900,
        learning_rate=0.03,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.9,
        min_child_weight=3,
        reg_alpha=1,
        reg_lambda=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)
    
    # 5. PREDICCIÓN
    preds = model.predict(X)
    
    # Métricas básicas para el log
    r2 = r2_score(y, preds)
    print(f"Modelo entrenado. R² Score: {r2:.4f}")
    
    # 6. PREPARAR TABLA FINAL
    # Usamos el DF filtrado (df_encoded) y le pegamos las columnas originales que necesitamos
    df_encoded['precio_justo_ia'] = preds
    df_encoded['ahorro_potencial'] = df_encoded['precio_justo_ia'] - df_encoded['final_price_pen']
    df_encoded['ahorro_pct'] = (df_encoded['ahorro_potencial'] / df_encoded['precio_justo_ia']) * 100
    
    # Renombramos para la tabla final
    final_df = df_encoded.rename(columns={
        'final_price_pen': 'precio_real',
        'store_original': 'tienda_origen',
        'tienda_reporte': 'tienda_grupo'
    })
    
    # Columnas a exportar a BigQuery
    cols_to_save = [
        'timestamp', 'product_id', 'name', 'tienda_origen', 'tienda_grupo',
        'precio_real', 'precio_justo_ia', 'ahorro_potencial', 
        'ahorro_pct', 'image_url',
        'cpu_score', 'ram_gb', 'storage_gb' # Extras útiles para dashboard
    ]
    
    print(f"   Guardando {len(final_df)} resultados en {DEST_TABLE}...")
    final_df[cols_to_save].to_gbq(
        destination_table=DEST_TABLE,
        project_id=PROJECT_ID,
        if_exists='replace'
    )
    print("Análisis completado.")

if __name__ == "__main__":
    run_ai_analysis()
