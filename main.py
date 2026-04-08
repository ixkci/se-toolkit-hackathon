from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
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
    is_urgent = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Fridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItemCreate(BaseModel):
    name: str
    is_urgent: bool = False

@app.get("/items/")
def get_items():
    db = SessionLocal()
    items = db.query(GroceryItem).order_by(
        GroceryItem.is_bought.asc(),          # 1. Некупленные выше купленных
        GroceryItem.is_urgent.desc(),         # 2. Срочные выше обычных
        func.lower(GroceryItem.name).asc()    # 3. По алфавиту без учета регистра (А = а)
    ).all()
    db.close()
    return items

@app.post("/items/")
def add_item(item: ItemCreate):
    db = SessionLocal()
    new_item = GroceryItem(name=item.name, is_urgent=item.is_urgent)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    db.close()
    return new_item

# 1. Эндпоинт для зачеркивания (is_bought)
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

# 2. Эндпоинт для мигалок (is_urgent)
@app.put("/items/{item_id}/toggle-urgent")
def toggle_item_urgency(item_id: int):
    db = SessionLocal()
    item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if item:
        item.is_urgent = not item.is_urgent
        db.commit()
        db.refresh(item)
    db.close()
    return item

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    db = SessionLocal()
    item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    db.close()
    return {"message": "Item deleted"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


import json
from openai import OpenAI
from pydantic import BaseModel

# Инициализация клиента OpenRouter
# ВАЖНО: Для продакшена ключи лучше прятать в .env файл, 
# но для локального теста можешь вставить его сюда.
OPENROUTER_API_KEY = "твой_скопированный_ключ_начинающийся_на_sk-or..."

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Модель для получения запроса от фронтенда
class RecipePrompt(BaseModel):
    prompt: str

@app.post("/items/ai-extract")
def extract_items_via_ai(data: RecipePrompt):
    # Системный промпт: жестко задаем правила для ИИ
    system_prompt = """
    You are a smart JSON-only shopping assistant. Extract grocery items and ingredients from the user's text.
    Return ONLY a valid JSON array of objects. Do NOT wrap it in markdown block quotes like ```json.
    Each object must have exactly two keys:
    - "name": string (the ingredient name)
    - "is_urgent": boolean (true if user implies it is urgently needed or required ASAP, otherwise false)
    """

    try:
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-7b-instruct:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.prompt}
            ],
            temperature=0.1 # Низкая температура, чтобы ИИ не фантазировал, а четко доставал данные
        )
        
        # Получаем текст ответа
        result_text = response.choices[0].message.content.strip()
        
        # Иногда ИИ всё равно оборачивает ответ в ```json ... ```, поэтому очищаем строку
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        # Превращаем текст в Python-список словарей
        items_to_add = json.loads(result_text)
        
        # Сохраняем спарсенные продукты в нашу базу данных
        db = SessionLocal()
        added_items = []
        for item in items_to_add:
            new_item = GroceryItem(name=item["name"], is_urgent=item.get("is_urgent", False))
            db.add(new_item)
            added_items.append(new_item)
            
        db.commit()
        for item in added_items:
            db.refresh(item)
        db.close()
        
        return {"message": "Success", "added_count": len(added_items)}

    except json.JSONDecodeError:
        return {"error": "AI returned invalid format", "raw_response": result_text}
    except Exception as e:
        return {"error": str(e)}