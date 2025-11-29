import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Price Monitoring API",
    description="API REST para almacenar y servir datos históricos de precios.",
    version="1.0.0"
)

# Variables de entorno
DB_HOST = os.getenv("DATABASE_HOST")
DB_USER = os.getenv("DATABASE_USER")
DB_NAME = os.getenv("DATABASE_NAME")

# --- BASE DE DATOS EN MEMORIA (Para Demo Rápida) ---
# En producción, esto se reemplazaría con queries SQL reales a Postgres
prices_db = [] 

class PriceEntry(BaseModel):
    product_id: str
    price: float
    timestamp: str
    name: str | None = None
    currency: str | None = "PEN"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Price API is Running"}

@app.get("/db-info")
def get_db_info():
    return {
        "DB_HOST": DB_HOST,
        "DB_USER": DB_USER,
        "DB_NAME": DB_NAME,
        "CONNECTION_STATUS": "Database connection logic goes here.",
        "TOTAL_RECORDS": len(prices_db) # Mostramos cuántos tenemos guardados
    }

@app.post("/prices")
async def create_price_entry(entry: PriceEntry):
    # Guardamos en nuestra "DB" en memoria
    prices_db.append(entry.dict())
    # Opcional: Mantener solo los últimos 100 para no llenar RAM
    if len(prices_db) > 200:
        prices_db.pop(0)
        
    print(f"Recibido: {entry.product_id} - {entry.price}")
    return {"message": "Price data received", "data": entry}

# --- NUEVO ENDPOINT PARA EL FRONTEND ---
@app.get("/prices")
def get_all_prices():
    """Devuelve los últimos precios registrados."""
    # Devolvemos la lista invertida para ver los más recientes primero
    return prices_db[::-1]

@app.get("/prices/{product_id}")
def get_price_history(product_id: str):
    # Filtrar por ID
    history = [p for p in prices_db if p['product_id'] == product_id]
    return {"product_id": product_id, "history": history}
