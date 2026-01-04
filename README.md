# Milk Tracker App

A modern mobile-first web application for tracking daily milk purchases with automatic cost calculation, bill splitting, and monthly email notifications.

## Features

- **Daily Milk Purchase Tracking**: Add milk purchases with quantity and price
- **Multi-Person Bill Splitting**: Automatically split costs among selected people
- **Daily & Monthly Summaries**: View cost breakdowns and purchase history
- **Monthly Email Notifications**: Automatic email summaries sent to all users
- **Mobile-First Design**: Responsive design optimized for mobile devices
- **Modern UI**: Clean, intuitive interface with gradient backgrounds

## Tech Stack

- **Backend**: FastAPI with Python
- **Database**: MongoDB with Motor (async driver)
- **Frontend**: Jinja2 templates with modern CSS
- **Email**: SMTP with scheduled notifications
- **Scheduler**: APScheduler for monthly email automation

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup MongoDB
- Install MongoDB locally or use MongoDB Atlas
- Update `MONGODB_URL` in `.env` file

### 3. Configure Environment Variables
Update `.env` file with your settings:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=milk_app
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SECRET_KEY=your_secret_key_here
```

### 4. Run the Application
```bash
python main.py
```

The app will be available at `http://localhost:8000`

## Usage

### 1. Add People
- Go to "People" tab
- Add names and email addresses of people who buy milk

### 2. Add Purchases
- Go to "Add Purchase" tab
- Enter quantity (liters) and price per liter
- Select people to split the cost
- View real-time cost calculation

### 3. View Summaries
- Home page shows today's summary and recent purchases
- Summary page shows monthly breakdowns and cost per person

### 4. Monthly Emails
- Automatic emails sent on 1st of each month at 9 AM
- Contains individual cost breakdown for each person

## API Endpoints

- `GET /` - Home page with daily summary
- `GET /add` - Add purchase form
- `POST /add` - Submit new purchase
- `GET /people` - People management page
- `POST /people` - Add new person
- `GET /summary` - Monthly summary page

## Database Schema

### People Collection
```json
{
  "_id": "ObjectId",
  "name": "string",
  "email": "string"
}
```

### Purchases Collection
```json
{
  "_id": "ObjectId",
  "date": "datetime",
  "quantity": "float",
  "price_per_liter": "float",
  "total_cost": "float",
  "people": ["string"],
  "cost_per_person": "float"
}
```

## Mobile-First Design

The app is designed with mobile users in mind:
- Touch-friendly buttons and form controls
- Optimized for small screens
- Responsive layout that works on all devices
- Modern gradient design with clean typography
- Easy navigation with tab-based interface

## Email Configuration

For Gmail SMTP:
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password in `EMAIL_PASSWORD`

## Deployment

The app can be deployed to any platform supporting Python:
- Heroku
- AWS EC2/ECS
- Google Cloud Run
- DigitalOcean App Platform

Make sure to:
1. Set environment variables in production
2. Use a production MongoDB instance
3. Configure proper SMTP settings
4. Set up SSL/HTTPS for security