from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.database import connect_to_mongo, close_mongo_connection
from app.main import *  # Import all routes and endpoints

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

# Use the existing app from app.main but with production lifespan
app.title = "Milk Tracker"
app.description = "Daily Milk Purchase Tracking System"
app.version = "1.0.0"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_prod:app", host="0.0.0.0", port=8000, workers=4)