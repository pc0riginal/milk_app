from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List
import os
import calendar
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import (
    connect_to_mongo, close_mongo_connection, create_person, get_people,
    create_purchase, get_daily_purchases, get_monthly_purchases, get_recent_purchases,
    get_milk_rate, update_milk_rate, update_purchase, delete_purchase, get_purchase_by_id,
    get_available_months
)
from .models import Person, PurchaseCreate
from .email_service import send_monthly_summary
from .pdf_service_new import generate_monthly_pdf

load_dotenv()

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    scheduler.start()
    # Schedule monthly email on 1st of every month at 9 AM
    scheduler.add_job(send_monthly_summary, 'cron', day=1, hour=9, minute=0)
    # Schedule monthly PDF generation on last day of month at 11 PM
    scheduler.add_job(generate_and_save_monthly_pdf, 'cron', day='last', hour=23, minute=0)
    yield
    scheduler.shutdown()
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    today = datetime.now()
    daily_purchases = await get_daily_purchases(today)
    recent_purchases = await get_recent_purchases(10)
    
    daily_summary = {
        "total_quantity": sum(p.quantity for p in daily_purchases),
        "total_cost": sum(p.total_cost for p in daily_purchases),
        "purchases": daily_purchases
    }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "daily_summary": daily_summary,
        "recent_purchases": recent_purchases
    })

@app.get("/add", response_class=HTMLResponse)
async def add_purchase_form(request: Request):
    people = await get_people()
    milk_rate = await get_milk_rate()
    return templates.TemplateResponse("add_purchase.html", {
        "request": request,
        "people": people,
        "milk_rate": milk_rate
    })

@app.post("/add", response_class=HTMLResponse)
async def add_purchase(
    request: Request,
    person: str = Form(...),
    quantity: float = Form(...),
    price_per_liter: float = Form(None),
    date: str = Form(None)
):
    try:
        purchase_date = None
        if date:
            purchase_date = datetime.strptime(date, "%Y-%m-%d")
        
        purchase_data = PurchaseCreate(
            person=person,
            quantity=quantity,
            price_per_liter=price_per_liter,
            date=purchase_date
        )
        
        await create_purchase(purchase_data)
        
        people_list = await get_people()
        milk_rate = await get_milk_rate()
        return templates.TemplateResponse("add_purchase.html", {
            "request": request,
            "people": people_list,
            "milk_rate": milk_rate,
            "message": "Purchase added successfully!"
        })
    except Exception as e:
        people_list = await get_people()
        milk_rate = await get_milk_rate()
        return templates.TemplateResponse("add_purchase.html", {
            "request": request,
            "people": people_list,
            "milk_rate": milk_rate,
            "error": str(e)
        })

@app.get("/people", response_class=HTMLResponse)
async def people_page(request: Request):
    people = await get_people()
    return templates.TemplateResponse("people.html", {
        "request": request,
        "people": people
    })

@app.post("/people", response_class=HTMLResponse)
async def add_person(
    request: Request,
    name: str = Form(...),
    email: str = Form(None)
):
    try:
        person = Person(name=name, email=email if email else None)
        await create_person(person)
        
        people = await get_people()
        return templates.TemplateResponse("people.html", {
            "request": request,
            "people": people,
            "message": f"{name} added successfully!"
        })
    except Exception as e:
        people = await get_people()
        return templates.TemplateResponse("people.html", {
            "request": request,
            "people": people,
            "error": str(e)
        })

@app.get("/summary", response_class=HTMLResponse)
async def summary_page(request: Request, month_year: str = None):
    available_months = await get_available_months()
    
    if not available_months:
        return templates.TemplateResponse("summary.html", {
            "request": request,
            "monthly_purchases": [],
            "total_quantity": 0,
            "total_cost": 0,
            "person_costs": {},
            "available_months": [],
            "selected_month": None,
            "selected_year": None,
            "calendar_data": None
        })
    
    # Parse month_year parameter or use first available
    if month_year:
        try:
            selected_month, selected_year = map(int, month_year.split('-'))
        except:
            selected_month = available_months[0]["month"]
            selected_year = available_months[0]["year"]
    else:
        selected_month = available_months[0]["month"]
        selected_year = available_months[0]["year"]
    
    monthly_purchases = await get_monthly_purchases(selected_year, selected_month)
    
    total_quantity = sum(p.quantity for p in monthly_purchases)
    total_cost = sum(p.total_cost for p in monthly_purchases)
    
    # Calculate cost per person
    person_costs = {}
    for purchase in monthly_purchases:
        person = purchase.person
        cost = purchase.total_cost
        if person:
            if person not in person_costs:
                person_costs[person] = 0
            person_costs[person] += cost
    
    # Generate calendar data
    calendar_data = generate_calendar_data(selected_year, selected_month, monthly_purchases)
    
    return templates.TemplateResponse("summary.html", {
        "request": request,
        "monthly_purchases": monthly_purchases,
        "total_quantity": total_quantity,
        "total_cost": total_cost,
        "person_costs": person_costs,
        "available_months": available_months,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "calendar_data": calendar_data
    })

def generate_calendar_data(year: int, month: int, purchases: list):
    cal = calendar.monthcalendar(year, month)
    
    # Group purchases by date and person
    daily_purchases = {}
    for purchase in purchases:
        date = purchase.date
        if date:
            day = date.day
            person = purchase.person
            quantity = purchase.quantity
            cost = purchase.total_cost
            
            if day not in daily_purchases:
                daily_purchases[day] = {}
            if person not in daily_purchases[day]:
                daily_purchases[day][person] = {'quantity': 0, 'cost': 0}
            
            daily_purchases[day][person]['quantity'] += quantity
            daily_purchases[day][person]['cost'] += cost
    
    # Build calendar structure
    calendar_weeks = []
    for week in cal:
        calendar_week = []
        for day in week:
            if day == 0:
                # Previous/next month day
                calendar_week.append({
                    'day': '',
                    'in_month': False,
                    'purchases': {}
                })
            else:
                calendar_week.append({
                    'day': day,
                    'in_month': True,
                    'purchases': daily_purchases.get(day, {})
                })
        calendar_weeks.append(calendar_week)
    
    return calendar_weeks

@app.get("/edit/{purchase_id}", response_class=HTMLResponse)
async def edit_purchase_form(request: Request, purchase_id: str):
    purchase = await get_purchase_by_id(purchase_id)
    if not purchase:
        return RedirectResponse(url="/", status_code=303)
    
    people = await get_people()
    milk_rate = await get_milk_rate()
    return templates.TemplateResponse("edit_purchase.html", {
        "request": request,
        "purchase": purchase,
        "people": people,
        "milk_rate": milk_rate
    })

@app.post("/edit/{purchase_id}", response_class=HTMLResponse)
async def edit_purchase(
    request: Request,
    purchase_id: str,
    person: str = Form(...),
    quantity: float = Form(...),
    price_per_liter: float = Form(None),
    date: str = Form(None)
):
    try:
        purchase_date = None
        if date:
            purchase_date = datetime.strptime(date, "%Y-%m-%d")
        
        purchase_data = PurchaseCreate(
            person=person,
            quantity=quantity,
            price_per_liter=price_per_liter,
            date=purchase_date
        )
        
        success = await update_purchase(purchase_id, purchase_data)
        if success:
            return RedirectResponse(url="/", status_code=303)
        else:
            raise Exception("Failed to update purchase")
    except Exception as e:
        purchase = await get_purchase_by_id(purchase_id)
        people = await get_people()
        milk_rate = await get_milk_rate()
        return templates.TemplateResponse("edit_purchase.html", {
            "request": request,
            "purchase": purchase,
            "people": people,
            "milk_rate": milk_rate,
            "error": str(e)
        })

@app.post("/delete/{purchase_id}")
async def delete_purchase_endpoint(purchase_id: str):
    await delete_purchase(purchase_id)
    return RedirectResponse(url="/", status_code=303)
async def update_settings(
    request: Request,
    milk_rate: float = Form(...)
):
    try:
        await update_milk_rate(milk_rate)
        return RedirectResponse(url="/add", status_code=303)
    except Exception as e:
        people_list = await get_people()
        current_rate = await get_milk_rate()
        return templates.TemplateResponse("add_purchase.html", {
            "request": request,
            "people": people_list,
            "milk_rate": current_rate,
            "error": f"Failed to update rate: {str(e)}"
        })
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
@app.post("/settings", response_class=HTMLResponse)
async def update_settings(
    request: Request,
    milk_rate: float = Form(...)
):
    try:
        await update_milk_rate(milk_rate)
        return RedirectResponse(url="/add", status_code=303)
    except Exception as e:
        people_list = await get_people()
        current_rate = await get_milk_rate()
        return templates.TemplateResponse("add_purchase.html", {
            "request": request,
            "people": people_list,
            "milk_rate": current_rate,
            "error": f"Failed to update rate: {str(e)}"
        })
@app.get("/download-pdf/{month_year}")
async def download_pdf(month_year: str):
    try:
        month, year = map(int, month_year.split('-'))
        print(f"Generating PDF for {month}/{year}")
        
        pdf_buffer = await generate_monthly_pdf(year, month)
        print(f"PDF generated, buffer size: {len(pdf_buffer.getvalue())}")
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        filename = f"milk_summary_{month_names[month-1]}_{year}.pdf"
        
        pdf_data = pdf_buffer.getvalue()
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"PDF Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url="/summary", status_code=303)
import io
async def generate_and_save_monthly_pdf():
    now = datetime.now()
    year = now.year
    month = now.month
    
    try:
        pdf_buffer = await generate_monthly_pdf(year, month)
        # Save PDF to local directory or send via email
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        filename = f"milk_summary_{month_names[month-1]}_{year}.pdf"
        
        # Save to pdfs directory
        os.makedirs("pdfs", exist_ok=True)
        with open(f"pdfs/{filename}", "wb") as f:
            f.write(pdf_buffer.read())
        
        print(f"Monthly PDF generated: {filename}")
    except Exception as e:
        print(f"Failed to generate monthly PDF: {str(e)}")