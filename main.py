from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import models, database # From Phase 1 setup

app = FastAPI()

# MongoDB Connection for Logging
MONGO_DETAILS = "mongodb://localhost:27017" # Use 'mongodb' if running inside Docker network
client = AsyncIOMotorClient(MONGO_DETAILS)
log_db = client.inventory_logs
logs_collection = log_db.get_collection("access_logs")

async def log_event(action: str, item_id: str = None):
    log_entry = {
        "timestamp": "2026-04-27T12:34:56Z",
        "method": "POST",
        "endpoint": "/item",
        "action": "ADD_INVENTORY"
    }
    await logs_collection.insert_one(log_entry)

@app.post("/item")
async def create_item(item_data: dict, db: Session = Depends(database.get_db)):
    
    new_item = models.Item(**item_data)
    db.add(new_item)
    db.commit()
    
    await log_event(action="CREATE_ITEM", item_id=new_item.id)
    
    return {"message": "Item created and event logged!"}

@app.get("/items")
async def list_items(db: Session = Depends(database.get_db)):
    
    # Log the access event to Mongo
    await log_event(action="LIST_ALL_ITEMS")
    return db.query(models.Item).all()