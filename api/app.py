import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Price Monitoring API",
    description="API REST para almacenar y servir datos históricos de precios.",
    version="1.0.0"
)
DB_HOST = os.getenv("DATABASE_HOST")
DB_USER = os.getenv("POSTGRES_USER")
DB_NAME = os.getenv("POSTGRES_DB")
class PriceEntry(BaseModel):
    product_id: str
    price: float
    timestamp: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Price API is Running"}

@app.get("/db-info")
def get_db_info():
    
    return {
        "DB_HOST": DB_HOST,
        "DB_USER": DB_USER,
        "DB_NAME": DB_NAME,
        "CONNECTION_STATUS": "Database connection logic goes here."
    }
@app.post("/prices")
async def create_price_entry(entry: PriceEntry):
    return {"message": "Price data received and saved (simulated)", "data": entry}
@app.get("/prices/{product_id}")
def get_price_history(product_id: str):
    return {"product_id": product_id, "history": []} # Devuelve datos simulados por ahora