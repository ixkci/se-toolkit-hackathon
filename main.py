import json
import os
import re
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
from sqlalchemy.orm import declarative_base, sessionmaker
import uvicorn
load_dotenv()

# --- DB SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./fridge.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GroceryItem(Base):
    __tablename__ = "grocery_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_bought = Column(Boolean, default=False)
    is_urgent = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# --- APP SETUP ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- AI SETUP (Groq) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class ItemCreate(BaseModel):
    name: str
    is_urgent: bool = False

class RecipePrompt(BaseModel):
    prompt: str

# --- ROUTES ---

# 1. Получение списка
@app.get("/items/")
def get_items():
    db = SessionLocal()
    items = db.query(GroceryItem).order_by(
        GroceryItem.is_bought.asc(), 
        GroceryItem.is_urgent.desc(), 
        func.lower(GroceryItem.name).asc()
    ).all()
    db.close()
    return items

# 2. ОБЫЧНОЕ ДОБАВЛЕНИЕ (Исправляет 405 Method Not Allowed)
@app.post("/items/")
def add_item(item: ItemCreate):
    db = SessionLocal()
    new_item = GroceryItem(name=item.name, is_urgent=item.is_urgent)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    db.close()
    return new_item

# 3. МАГИЧЕСКОЕ ДОБАВЛЕНИЕ (Groq AI)
@app.post("/items/ai-extract")
def extract_items_via_ai(data: RecipePrompt):
    print(f"DEBUG: AI prompt: {data.prompt}")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Return ONLY a JSON array: [{\"name\": \"item\", \"is_urgent\": bool}]. No text or markdown."},
            {"role": "user", "content": data.prompt}
        ],
        "temperature": 0
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=15)
        res_json = response.json()
        result_text = res_json['choices'][0]['message']['content'].strip()
        
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        clean_json = json_match.group(0) if json_match else result_text
        items_to_add = json.loads(clean_json)
        
        db = SessionLocal()
        for item in items_to_add:
            db.add(GroceryItem(name=item.get("name"), is_urgent=item.get("is_urgent", False)))
        db.commit()
        db.close()
        return {"status": "success"}
    except Exception as e:
        print(f"AI ERROR: {str(e)}")
        return {"error": str(e)}

# 4. Переключатели и удаление
@app.put("/items/{item_id}/toggle")
def toggle_item(item_id: int):
    db = SessionLocal()
    item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if item:
        item.is_bought = not item.is_bought
        db.commit()
    db.close()
    return {"ok": True}

@app.put("/items/{item_id}/toggle-urgent")
def toggle_urgent(item_id: int):
    db = SessionLocal()
    item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if item:
        item.is_urgent = not item.is_urgent
        db.commit()
    db.close()
    return {"ok": True}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    db = SessionLocal()
    item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    db.close()
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)