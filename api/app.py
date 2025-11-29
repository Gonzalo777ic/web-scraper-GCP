import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
app = FastAPI(
    title="Price Monitoring API",
    description="API REST para almacenar y servir datos históricos de precios.",
    version="1.1.0"
)


DB_HOST = os.getenv("DATABASE_HOST")
DB_USER = os.getenv("DATABASE_USER")
DB_NAME = os.getenv("DATABASE_NAME")


prices_db = [] 

class PriceEntry(BaseModel):
    product_id: str
    price: float
    timestamp: str
    name: Optional[str] = None
    currency: Optional[str] = "PEN"
    

    image_url: Optional[str] = None  
    store: Optional[str] = None      


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Price API is Running"}

@app.get("/db-info")
def get_db_info():
    return {
        "DB_HOST": DB_HOST,
        "DB_USER": DB_USER,
        "DB_NAME": DB_NAME,
        "CONNECTION_STATUS": "OK",
        "TOTAL_RECORDS": len(prices_db)
    }

@app.post("/prices")
async def create_price_entry(entry: PriceEntry):
    prices_db.append(entry.dict())

    if len(prices_db) > 300:
        prices_db.pop(0)
    return {"message": "Price data received", "data": entry}

@app.get("/prices")
def get_all_prices():
    """Devuelve los últimos precios registrados (invertidos)."""
    return prices_db[::-1]

@app.get("/prices/{product_id}")
def get_price_history(product_id: str):
    history = [p for p in prices_db if p['product_id'] == product_id]
    return {"product_id": product_id, "history": history}
