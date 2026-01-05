from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..database import get_people, create_person
from ..models import Person

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def people_page(request: Request):
    people = await get_people()
    return templates.TemplateResponse("people.html", {
        "request": request,
        "people": people
    })

@router.post("/", response_class=HTMLResponse)
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