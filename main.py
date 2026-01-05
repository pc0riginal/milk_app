from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from app.database import connect_to_mongo, close_mongo_connection
from app.routers import purchases, people, summary
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.email_service import send_monthly_summary

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    scheduler.start()
    # Schedule monthly email on 1st of every month at 9 AM
    scheduler.add_job(send_monthly_summary, 'cron', day=1, hour=9, minute=0)
    yield
    # Shutdown
    scheduler.shutdown()
    await close_mongo_connection()

app = FastAPI(
    title="Milk Tracker App",
    description="Daily milk purchase tracking with cost calculation and bill splitting",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(purchases.router)
app.include_router(people.router, prefix="/people")
app.include_router(summary.router, prefix="/summary")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)