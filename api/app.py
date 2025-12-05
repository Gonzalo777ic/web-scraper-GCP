import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- IMPORTANTE
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Price Monitoring API (SQL)", version="2.2.0")

# --- CONFIGURACIÓN DE CORS (Permite que Next.js se conecte) ---
origins = [
    "http://localhost:3000",  # Tu desarrollo local
    "https://tu-proyecto.vercel.app", # Tu futuro deploy en Vercel
    "*" # Permitir todo (solo para esta demo, úsalo con precaución)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------------------------------------------------------------

DB_HOST = os.getenv("DATABASE_HOST")
DB_USER = os.getenv("DATABASE_USER")
DB_NAME = os.getenv("DATABASE_NAME")
DB_PASS = os.getenv("POSTGRES_PASSWORD") 

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ... (MANTÉN EL RESTO DE TU CÓDIGO DE MODELOS DB Y PYDANTIC IGUAL) ...
# Copia aquí las clases DailyPrice y PriceEntry del código anterior
class DailyPrice(Base):
    __tablename__ = "daily_prices"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    currency = Column(String)
    store = Column(String)
    image_url = Column(String)
    scrape_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    return {"status": "ok", "message": "Price API (SQL Persistent) is Running"}

@app.get("/db-info")
def get_db_info():
    try:
        db = SessionLocal()
        count = db.query(DailyPrice).count()
        db.close()
        status = "Connected"
    except Exception as e:
        status = f"Error: {str(e)}"
        count = -1

    return {
        "DB_HOST": DB_HOST,
        "CONNECTION_STATUS": status,
        "TOTAL_RECORDS_IN_DB": count
    }

@app.post("/prices")
async def create_price_entry(entry: PriceEntry):
    db = SessionLocal()
    try:
        sql = text("""
            INSERT INTO daily_prices (product_id, name, price, currency, store, image_url, scrape_date)
            VALUES (:pid, :name, :price, :curr, :store, :img, CURRENT_DATE)
            ON CONFLICT (product_id, store, scrape_date) 
            DO UPDATE SET price = :price, created_at = CURRENT_TIMESTAMP
        """)
        
        db.execute(sql, {
            "pid": entry.product_id,
            "name": entry.name,
            "price": entry.price,
            "curr": entry.currency,
            "store": entry.store,
            "img": entry.image_url
        })
        db.commit()
        return {"message": "Saved to SQL", "product": entry.product_id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error insertando {entry.product_id}: {e}")
        return {"message": "Error saving", "error": str(e)}
    finally:
        db.close()

@app.get("/prices")
def get_all_prices():
    db = SessionLocal()
    try:
        results = db.query(DailyPrice).order_by(DailyPrice.created_at.desc()).all()
        return results
    finally:
        db.close()
