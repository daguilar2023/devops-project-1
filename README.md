# Blog Application (Flask + SQLite)

A minimal blog system built with **Flask**, **SQLAlchemy**, and **SQLite**.  
The app allows admins to create, edit, delete, archive/unarchive posts, and track all actions in a log.  
The homepage displays all public (non-archived) posts.

---

## Features

- **CRUD functionality**: Create, Read, Update, Delete blog posts.
- **Persistent storage**: Data is stored in a local SQLite database (`blog.db`).
- **Archiving**: Posts can be archived (hidden from public view) and later unarchived.
- **Action logs**: Every admin operation is recorded in a history log for accountability.

---

## Requirements

- Python 3.10+
- pip (Python package manager)
- Virtual environment recommended (`venv` or `.venv`)

---

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/daguilar2023/devops-project-1.git
   cd devops-project-1
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # if you are on Windows, do: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run app.py**

   ```bash
   python3 app.py
   ```

5. **Initialize the database (if step 4 didnt work)**

   ```bash
   flask --app app init-db
   ```

6. **Run the application (if step 4 didint work, and step 5 works)**

   ```bash
   flask --app app run --debug
   ```

7. **Access the app**
   - Public homepage: [http://localhost:5000/](http://localhost:5000/)
   - Admin panel: [http://localhost:5000/admin](http://localhost:5000/admin)

---

## Project Structure

```
.
├── app.py                 # Flask application (routes, models, logic)
├── blog.db                # SQLite database (generated after init-db)
├── requirements.txt       # Project dependencies
├── templates/             # HTML templates (public, admin, history, etc.)
├── static/                # CSS/JS (if any)
└── README.md              # Setup and usage instructions
```
