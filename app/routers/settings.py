from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..database import get_milk_rate, update_milk_rate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    milk_rate = await get_milk_rate()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "milk_rate": milk_rate
    })

@router.post("/milk-rate", response_class=HTMLResponse)
async def update_milk_rate_route(
    request: Request,
    milk_rate: float = Form(...)
):
    try:
        await update_milk_rate(milk_rate)
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "milk_rate": milk_rate,
            "message": "Milk rate updated successfully!"
        })
    except Exception as e:
        current_rate = await get_milk_rate()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "milk_rate": current_rate,
            "error": str(e)
        })