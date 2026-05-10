# 📋 TaskFlow — Smart Task Management System

A full-stack task management web app built with **Flask + PostgreSQL + WebSockets + Pandas/NumPy**.

**Built by:** Allibad Pujitha  
**Stack:** Python, Flask, PostgreSQL, Flask-SocketIO, Pandas, NumPy, HTML/CSS

---

## 🚀 Features

- ✅ User Registration, Login, Logout (with bcrypt password hashing)
- ✅ Full REST API — Add, Update, Delete, Get Tasks
- ✅ PostgreSQL database with proper relational structure
- ✅ Analytics using Pandas & NumPy (totals, completion %, priority breakdown)
- ✅ Real-time WebSocket notifications on task changes
- ✅ Clean, responsive dark-themed frontend
- ✅ Filter tasks by status and priority

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/smart-task-manager.git
cd smart-task-manager
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL
Make sure PostgreSQL is installed and running, then:
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE taskmanager;"

# Run the schema
psql -U postgres -d taskmanager -f schema.sql
```

### 5. Configure environment variables
Create a `.env` file or set these variables:
```
DB_HOST=localhost
DB_NAME=taskmanager
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

Or edit the `get_db()` function in `app.py` directly with your credentials.

### 6. Run the application
```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | Login user |
| POST | `/api/logout` | Logout user |
| GET | `/api/tasks` | Get all tasks |
| POST | `/api/tasks` | Add new task |
| PUT | `/api/tasks/<id>` | Update task |
| DELETE | `/api/tasks/<id>` | Delete task |
| GET | `/api/analytics` | Get analytics data |

---

## 📊 Analytics (Pandas + NumPy)

The `/api/analytics` endpoint uses:
- **Pandas** to load task data into a DataFrame
- **NumPy** `np.sum()` and `np.mean()` to calculate counts and completion percentage
- **Pandas** `value_counts()` for priority breakdown

---

## ⚡ WebSockets

Real-time notifications are powered by **Flask-SocketIO**. When any task is added, updated, or deleted, all connected browsers instantly receive a notification — no page refresh needed.

Events emitted:
- `task_added` — when a new task is created
- `task_updated` — when a task is modified
- `task_deleted` — when a task is removed

---

## 🗂️ Project Structure

```
smart_task_manager/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── schema.sql          # PostgreSQL database schema
├── README.md           # This file
└── templates/
    ├── login.html      # Login page
    ├── register.html   # Registration page
    └── dashboard.html  # Main dashboard with tasks + analytics
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python + Flask | Backend web framework |
| PostgreSQL | Relational database |
| Flask-SocketIO | WebSocket real-time events |
| Flask-Bcrypt | Password hashing |
| Pandas + NumPy | Analytics calculations |
| HTML + CSS | Frontend UI |
| Socket.IO (JS) | Client-side WebSocket |

Smart Task Management System
Author: Allibad Pujitha
