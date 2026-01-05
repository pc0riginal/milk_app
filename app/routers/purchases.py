from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from ..database import (
    get_daily_purchases, get_recent_purchases, create_purchase, 
    get_people, get_milk_rate, get_purchase_by_id, update_purchase, delete_purchase,
    update_milk_rate
)
from ..models import PurchaseCreate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
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

@router.get("/add", response_class=HTMLResponse)
async def add_purchase_form(request: Request):
    people = await get_people()
    milk_rate = await get_milk_rate()
    return templates.TemplateResponse("add_purchase.html", {
        "request": request,
        "people": people,
        "milk_rate": milk_rate
    })

@router.post("/add", response_class=HTMLResponse)
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

@router.get("/edit/{purchase_id}", response_class=HTMLResponse)
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

@router.post("/edit/{purchase_id}", response_class=HTMLResponse)
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
        
        await update_purchase(purchase_id, purchase_data)
        return RedirectResponse(url="/", status_code=303)
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

@router.post("/delete/{purchase_id}")
async def delete_purchase_route(purchase_id: str):
    await delete_purchase(purchase_id)
    return RedirectResponse(url="/", status_code=303)

@router.post("/settings")
async def update_settings(milk_rate: float = Form(...)):
    await update_milk_rate(milk_rate)
    return RedirectResponse(url="/add", status_code=303)