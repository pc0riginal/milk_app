import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List
from .database import get_monthly_purchases, get_people

async def send_monthly_summary():
    now = datetime.now()
    last_month = now.month - 1 if now.month > 1 else 12
    year = now.year if now.month > 1 else now.year - 1
    
    purchases = await get_monthly_purchases(year, last_month)
    people = await get_people()
    
    if not purchases:
        return
    
    total_cost = sum(p.get('total_cost', 0) for p in purchases)
    total_quantity = sum(p.get('quantity', 0) for p in purchases)
    
    # Group by person
    person_costs = {}
    for purchase in purchases:
        person = purchase.get('person')
        cost = purchase.get('total_cost', 0)
        if person:
            if person not in person_costs:
                person_costs[person] = 0
            person_costs[person] += cost
    
    # Send email to each person
    for person in people:
        if person.name in person_costs:
            await send_email_to_person(
                person.email, 
                person.name, 
                person_costs[person.name],
                total_quantity,
                len([p for p in purchases if p.get('person') == person.name]),
                f"{year}-{last_month:02d}"
            )

async def send_email_to_person(email: str, name: str, cost: float, quantity: float, purchase_count: int, month: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email
    msg['Subject'] = f"Monthly Milk Summary - {month}"
    
    body = f"""
    Hi {name},
    
    Here's your milk purchase summary for {month}:
    
    • Your total cost: ₹{cost:.2f}
    • Total milk quantity: {quantity:.1f} liters
    • Number of purchases: {purchase_count}
    
    Thank you for using Milk Tracker!
    
    Best regards,
    Milk Tracker Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, email, text)
        server.quit()
        print(f"Email sent to {name} ({email})")
    except Exception as e:
        print(f"Failed to send email to {name}: {str(e)}")