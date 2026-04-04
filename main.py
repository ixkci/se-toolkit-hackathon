from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import uvicorn

SQLALCHEMY_DATABASE_URL = "sqlite:///./fridge.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GroceryItem(Base):
    __tablename__ = "grocery_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_bought = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shared Fridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItemCreate(BaseModel):
    name: str

@app.get("/items/")
def get_items():
    db = SessionLocal()
    items = db.query(GroceryItem).all()
    db.close()
    return items

@app.post("/items/")
def add_item(item: ItemCreate):
    db = SessionLocal()
    new_item = GroceryItem(name=item.name)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    db.close()
    return new_item

@app.put("/items/{item_id}/toggle")
def toggle_item_status(item_id: int):
    db = SessionLocal()
    item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if item:
        item.is_bought = not item.is_bought
        db.commit()
        db.refresh(item)
    db.close()
    return item

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)