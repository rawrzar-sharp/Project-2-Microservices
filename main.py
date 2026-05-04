from fastapi import FastAPI, Depends, Request #helps in requesting as theres middlewear1, .... --> response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import HTTPException # helps with error responses https://fastapi.tiangolo.com/tutorial/handling-errors/?h=fastapi+import+httpexception#reuse-fastapis-exception-handlers
from motor.motor_asyncio import AsyncIOMotorClient # Might be a bit confusing buuttt.. asynchronous client Following Phase 3 uses Motor https://fastapi.tiangolo.com/advanced/async-tests/?h=#run-it 
import datetime
import models, database # From Phase 1 setup

app = FastAPI()
models.Base.metadata.create_all(bind=database.engine)
templates = Jinja2Templates(directory="templates") #required due to using Jinja within main_page.html (phase1) oh yeah and templates helps to find html files in the screens folder, so we can render them in our routes
models.Base.metadata.create_all(bind=database.engine)

# MongoDB Connection for Logging
MONGO_DETAILS = "mongodb://user:rafdah@mongodb_db:27017" # Use 'mongodb' if running inside Docker network
client = AsyncIOMotorClient(MONGO_DETAILS)
log_db = client.inventory_logs
logs_collection = log_db.get_collection("access_logs")

# Middlewear: https://fastapi.tiangolo.com/tutorial/middleware/#create-a-middleware
@app.middleware("http")
async def phase3_logging_middleware(request: Request, call_next):
    # First and foremost, Let the requests go to its routes
    response = await call_next(request)
    
    # Second of all, Actions based on its endpoint and method
    action = "UNKNOWN"
    if request.method == "POST" and "/item" in request.url.path: #post = add invent.
        action = "ADD_INVENTORY"
    elif request.method == "GET" and "/items" in request.url.path: # get = list invent.
        action = "LIST_INVENTORY"
        
    # Third and lastly, Use a MongoDB client for the api_logs mentioned in the instructions.
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z", #Real-time stamp following this reference: https://pymongo.readthedocs.io/en/stable/api/bson/timestamp.html and https://stackabuse.com/tools/timestamp-converter/
        "method": request.method,                                  # Dynamic method (GET/POST)
        "endpoint": request.url.path,                              #dynamic endpoint
        "action": action,
        "user_agent": request.headers.get("user-agent", "Unknown") #phase 3 requirement, get user-agent from request headers, unknown if not there
    }
    
    # 4. asynchronously insert this JSON document into a MongoDB collection named api_logs:
    await logs_collection.insert_one(log_entry)
    
    return response

# POST function
@app.post("/item")
async def create_item(item_data: dict, db: Session = Depends(database.get_db)):
    
    new_item = models.Item(**item_data)
    db.add(new_item)
    db.commit()
    return {"message": "Item created and logged :3!"}

#GET function
@app.get("/items")
async def list_items(db: Session = Depends(database.get_db)):
    return db.query(models.Item).all()

#GET function for viewing ONLY ONNEEE item.
@app.get("/item/{item_id}")
async def get_item(item_id: str, db: Session = Depends(database.get_db)):
    # Look up the item by its ID
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

#PUT function for editing the item
@app.put("/item/{item_id}")
async def update_item(item_id: str, item_data: dict, db: Session = Depends(database.get_db)):
    # Find the item
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found :C")
    
    # Update the fields
    for key, value in item_data.items():
        setattr(item, key, value)
        
    db.commit()
    return {"message": "Item updated successfully!"}

#DELETE function for obv deleting it
@app.delete("/item/{item_id}")
async def delete_item(item_id: str, db: Session = Depends(database.get_db)):
    # Find the item and delete it
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully!"}



@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request, db: Session = Depends(database.get_db)):
    inventory_items = db.query(models.Item).all()

    return templates.TemplateResponse(
        request=request, 
        name="main_page.html", 
        context={"items": inventory_items}
    )

# GET /create - Show create form
@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="create.html",
        context={"item": None}
    )

# POST /create - Handle form submission for creating items
@app.post("/create")
async def create_item_form(request: Request, db: Session = Depends(database.get_db)):
    try:
        form_data = await request.form()
        
        new_item = models.Item(
            short_name=form_data.get("short_name"),
            description=form_data.get("description"),
            price=int(form_data.get("price")),
            amount=int(form_data.get("amount"))
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        # Redirect to the newly created item's view page
        return RedirectResponse(url=f"/view/{new_item.id}", status_code=303)
    except Exception as e:
        print(f"Error creating item: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")

# GET /view/{item_id} - Show item details
@app.get("/view/{item_id}", response_class=HTMLResponse)
async def view_item_page(request: Request, item_id: str, db: Session = Depends(database.get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return templates.TemplateResponse(
        request=request,
        name="view.html",
        context={"item": item}
    )

# GET /edit/{item_id} - Show edit form
@app.get("/edit/{item_id}", response_class=HTMLResponse)
async def edit_item_page(request: Request, item_id: str, db: Session = Depends(database.get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return templates.TemplateResponse(
        request=request,
        name="create.html",
        context={"item": item}
    )

# POST /edit/{item_id} - Handle form submission for updating items
@app.post("/edit/{item_id}")
async def update_item_form(request: Request, item_id: str, db: Session = Depends(database.get_db)):
    try:
        item = db.query(models.Item).filter(models.Item.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        form_data = await request.form()
        
        # Update the fields
        item.short_name = form_data.get("short_name")
        item.description = form_data.get("description")
        item.price = int(form_data.get("price"))
        item.amount = int(form_data.get("amount"))
        
        db.commit()
        db.refresh(item)
        
        # Redirect to the item's view page
        return RedirectResponse(url=f"/view/{item.id}", status_code=303)
    except Exception as e:
        print(f"Error updating item: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")
    
    