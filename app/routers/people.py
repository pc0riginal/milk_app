from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId

from ..database import get_people, create_person, get_database
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

@router.post("/delete/{person_id}")
async def delete_person(person_id: str):
    db = get_database()
    await db.people.delete_one({"_id": ObjectId(person_id)})
    return RedirectResponse(url="/people", status_code=303)

@router.get("/edit/{person_id}", response_class=HTMLResponse)
async def edit_person_page(request: Request, person_id: str):
    db = get_database()
    person_data = await db.people.find_one({"_id": ObjectId(person_id)})
    if person_data:
        person = Person(**person_data)
        return templates.TemplateResponse("edit_person.html", {
            "request": request,
            "person": person
        })
    return RedirectResponse(url="/people", status_code=303)

@router.post("/edit/{person_id}")
async def update_person(
    person_id: str,
    name: str = Form(...),
    email: str = Form(None)
):
    db = get_database()
    await db.people.update_one(
        {"_id": ObjectId(person_id)},
        {"$set": {"name": name, "email": email if email else None}}
    )
    return RedirectResponse(url="/people", status_code=303)