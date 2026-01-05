"""
Run this script once to create database indexes for better performance
Usage: python create_indexes.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def create_indexes():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME")]
    
    # Create index on purchases.date for faster date-based queries
    await db.purchases.create_index([("date", -1)])
    
    # Create compound index for date range queries
    await db.purchases.create_index([("date", -1), ("person", 1)])
    
    # Create index on people collection
    await db.people.create_index([("name", 1)])
    
    print("Database indexes created successfully")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
