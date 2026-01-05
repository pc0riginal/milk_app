import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from datetime import datetime, timedelta
from .models import Person, PurchaseCreate, Settings, Purchase
from bson import ObjectId
from .cache import get_cached_milk_rate, set_cached_milk_rate, clear_milk_rate_cache

class Database:
    client: AsyncIOMotorClient = None
    
db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(
        os.getenv("MONGODB_URL"),
        maxPoolSize=10,
        minPoolSize=1,
        maxIdleTimeMS=45000,
        serverSelectionTimeoutMS=5000
    )
    
async def close_mongo_connection():
    db.client.close()

def get_database():
    return db.client[os.getenv("DATABASE_NAME")]

async def create_person(person: Person):
    database = get_database()
    result = await database.people.insert_one(person.model_dump(by_alias=True, exclude_unset=True))
    return str(result.inserted_id)

async def get_people():
    database = get_database()
    people = []
    async for person in database.people.find():
        people.append(Person(**person))
    return people

async def get_milk_rate():
    cached = get_cached_milk_rate()
    if cached is not None:
        return cached
    
    database = get_database()
    settings = await database.settings.find_one()
    rate = settings.get('milk_rate', 60.0) if settings else 60.0
    set_cached_milk_rate(rate)
    return rate

async def update_milk_rate(rate: float):
    database = get_database()
    await database.settings.update_one(
        {},
        {"$set": {"milk_rate": rate}},
        upsert=True
    )
    clear_milk_rate_cache()

async def create_purchase(purchase_data: PurchaseCreate):
    # Get global milk rate if not provided
    price_per_liter = purchase_data.price_per_liter
    if price_per_liter is None:
        price_per_liter = await get_milk_rate()
    
    total_cost = purchase_data.quantity * price_per_liter
    
    purchase = {
        "date": purchase_data.date or datetime.now(),
        "person": purchase_data.person,
        "quantity": purchase_data.quantity,
        "price_per_liter": price_per_liter,
        "total_cost": total_cost
    }
    
    database = get_database()
    result = await database.purchases.insert_one(purchase)
    return str(result.inserted_id)

async def update_purchase(purchase_id: str, purchase_data: PurchaseCreate):
    price_per_liter = purchase_data.price_per_liter
    if price_per_liter is None:
        price_per_liter = await get_milk_rate()
    
    total_cost = purchase_data.quantity * price_per_liter
    
    update_data = {
        "person": purchase_data.person,
        "quantity": purchase_data.quantity,
        "price_per_liter": price_per_liter,
        "total_cost": total_cost
    }
    
    if purchase_data.date:
        update_data["date"] = purchase_data.date
    
    database = get_database()
    result = await database.purchases.update_one(
        {"_id": ObjectId(purchase_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def delete_purchase(purchase_id: str):
    database = get_database()
    result = await database.purchases.delete_one({"_id": ObjectId(purchase_id)})
    return result.deleted_count > 0

async def get_available_months():
    database = get_database()
    pipeline = [
        {"$group": {
            "_id": {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"}
            }
        }},
        {"$sort": {"_id.year": -1, "_id.month": -1}}
    ]
    
    months = []
    async for result in database.purchases.aggregate(pipeline):
        months.append({
            "year": result["_id"]["year"],
            "month": result["_id"]["month"]
        })
    return months
    database = get_database()
    purchase = await database.purchases.find_one({"_id": ObjectId(purchase_id)})
    if purchase:
        if 'person' not in purchase and 'people' in purchase:
            # Handle old schema
            return None  # Skip old format for editing
        return Purchase(**purchase)
    return None

async def get_daily_purchases(date: datetime):
    database = get_database()
    start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)
    
    purchases = []
    async for purchase in database.purchases.find({
        "date": {"$gte": start_date, "$lt": end_date}
    }).sort("date", -1):
        if 'person' not in purchase and 'people' in purchase:
            for person in purchase['people']:
                new_purchase = {
                    '_id': purchase['_id'],
                    'date': purchase['date'],
                    'person': person,
                    'quantity': purchase['quantity'],
                    'price_per_liter': purchase['price_per_liter'],
                    'total_cost': purchase.get('cost_per_person', purchase['total_cost'])
                }
                purchases.append(Purchase(**new_purchase))
        elif 'person' in purchase:
            purchases.append(Purchase(**purchase))
    return purchases

async def get_monthly_purchases(year: int, month: int):
    database = get_database()
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    purchases = []
    async for purchase in database.purchases.find({
        "date": {"$gte": start_date, "$lt": end_date}
    }).sort("date", -1):
        if 'person' not in purchase and 'people' in purchase:
            for person in purchase['people']:
                new_purchase = {
                    '_id': purchase['_id'],
                    'date': purchase['date'],
                    'person': person,
                    'quantity': purchase['quantity'],
                    'price_per_liter': purchase['price_per_liter'],
                    'total_cost': purchase.get('cost_per_person', purchase['total_cost'])
                }
                purchases.append(Purchase(**new_purchase))
        elif 'person' in purchase:
            purchases.append(Purchase(**purchase))
    return purchases

async def get_recent_purchases(limit: int = 10):
    database = get_database()
    purchases = []
    async for purchase in database.purchases.find().sort("date", -1).limit(limit):
        # Handle old schema with 'people' field
        if 'person' not in purchase and 'people' in purchase:
            for person in purchase['people']:
                new_purchase = {
                    '_id': purchase['_id'],
                    'date': purchase['date'],
                    'person': person,
                    'quantity': purchase['quantity'],
                    'price_per_liter': purchase['price_per_liter'],
                    'total_cost': purchase.get('cost_per_person', purchase['total_cost'])
                }
                purchases.append(Purchase(**new_purchase))
        elif 'person' in purchase:
            purchases.append(Purchase(**purchase))
    return purchases
async def get_purchase_by_id(purchase_id: str):
    database = get_database()
    purchase = await database.purchases.find_one({"_id": ObjectId(purchase_id)})
    if purchase:
        if 'person' not in purchase and 'people' in purchase:
            # Handle old schema
            return None  # Skip old format for editing
        return Purchase(**purchase)
    return None