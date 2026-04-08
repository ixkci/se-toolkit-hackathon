from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# --- КОНФИГУРАЦИЯ ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./fridge.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ItemModel(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category = Column(String, default="Other")
    is_urgent = Column(Boolean, default=False)
    is_bought = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

class ItemCreate(BaseModel):
    name: str
    category: str = "Other"
    is_urgent: bool = False

class ItemResponse(BaseModel):
    id: int
    name: str
    category: str
    is_urgent: bool
    is_bought: bool
    class Config:
        from_attributes = True

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.get("/items/", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(ItemModel).order_by(ItemModel.is_bought.asc(), ItemModel.is_urgent.desc(), ItemModel.name.asc()).all()

@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = ItemModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/items/{item_id}/toggle")
def toggle_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if item:
        item.is_bought = not item.is_bought
        if item.is_bought:
            item.is_urgent = False
    db.commit()
    return {"status": "success"}

@app.put("/items/{item_id}/toggle-urgent")
def toggle_urgent(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if item: item.is_urgent = not item.is_urgent
    db.commit()
    return {"status": "success"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if item: db.delete(item)
    db.commit()
    return {"status": "deleted"}
