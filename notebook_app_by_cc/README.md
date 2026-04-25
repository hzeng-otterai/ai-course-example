# Notebook App

A full-stack collaborative notebook application with rich text editing, user authentication, and shareable page links.

## Tech Stack

- **Frontend:** React 19, Vite, TipTap (rich text editor), Tailwind CSS, React Query
- **Backend:** Django, Django REST Framework, JWT authentication, SQLite

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate        # first time only
python manage.py runserver      # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

Start the backend first, then the frontend. The Vite dev server proxies `/api` requests to `localhost:8000` automatically.

Open **http://localhost:5173** in your browser.

## Features

- User registration and login (JWT-based)
- Create and manage notebooks and pages
- Rich text editing with auto-save
- Shareable read-only page links via UUID tokens
