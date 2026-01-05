from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import calendar
from datetime import datetime

from ..database import get_available_months, get_monthly_purchases
from ..pdf_service_new import generate_monthly_pdf

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
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

@router.get("/download-pdf")
async def download_monthly_pdf(month_year: str = None):
    if month_year:
        try:
            month, year = map(int, month_year.split('-'))
        except:
            # Default to current month
            now = datetime.now()
            month, year = now.month, now.year
    else:
        # Default to current month
        now = datetime.now()
        month, year = now.month, now.year
    
    pdf_buffer = await generate_monthly_pdf(year, month)
    
    filename = f"milk_summary_{year}_{month:02d}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )