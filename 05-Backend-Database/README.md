# Backend + Database (Python + FastAPI + SQLite) — SDLC Stage 8

**ABC Learning Solutions — Training Management Portal**

> Same API as the previous backend (`04-Backend-Python`), but the data now
> lives in a **real database** and **survives restarts.** This is SDLC
> **Stage 8: Database Development.**

---

## 🧠 The one big idea

| | In-memory backend (04) | **Database backend (05)** |
|--|------------------------|---------------------------|
| Where data lives | computer's memory (RAM) | a file on disk (`training.db`) |
| Add a student, restart server | ❌ **gone** | ✅ **still there** |
| Analogy | a whiteboard (wiped on reset) | a **filing cabinet** (remembers overnight) |

> 🎤 **Live class demo:** add a student → stop the server → start it again →
> the student is still there. That single moment *is* the lesson.

## 📁 Folder structure

```
05-Backend-Database/
├── main.py            # app + startup that builds/seeds the DB
├── database.py        # ⭐ NEW: the database connection + first-time seeding
├── models.py          # now defines real TABLES (SQLModel, table=True)
├── auth.py            # users looked up FROM the database
├── requirements.txt   # adds: sqlmodel
├── training.db        # the database file (auto-created on first run)
└── routers/           # same modules, now running real SQL
    ├── students.py    # SELECT / INSERT / UPDATE / DELETE
    ├── trainers.py
    ├── courses.py
    ├── attendance.py
    ├── certificates.py
    └── reports.py
```

## ▶️ How to run

```bash
cd 05-Backend-Database
python -m pip install -r requirements.txt      # first time only
python -m uvicorn main:app --reload
```

Open the interactive API page: **http://127.0.0.1:8000/docs**

The first run **creates `training.db` and seeds it** automatically. Delete that
file any time to reset to the starter data.

## 🔑 Demo logins (unchanged)

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin |
| `trainer` | `trainer123` | Trainer |
| `student` | `student123` | Student |

## 🗄️ What changed from the in-memory backend (the teaching diff)

| Concern | Before (04) | After (05) |
|---------|-------------|------------|
| Storage | Python lists in `data.py` | SQLite tables via `database.py` |
| Models | plain Pydantic | **SQLModel** (`table=True`) = real tables |
| Reading | `data.students` | `session.exec(select(StudentDB)).all()` → **SQL SELECT** |
| Writing | `list.append()` | `session.add(); session.commit()` → **SQL INSERT** |
| Survives restart? | No | **Yes** |

Notice the **routers, auth, and API are almost identical** — only the *data
layer* changed. That's the payoff of clean architecture (separation of concerns).

## 🎓 Concepts this stage teaches

- **What a database is** — persistent, structured storage (tables, rows, columns).
- **Tables & primary keys** — each model is a table; the `id` uniquely labels a row.
- **CRUD as SQL** — GET→SELECT, POST→INSERT, PUT→UPDATE, DELETE→DELETE.
- **ORM** — SQLModel lets us use Python objects instead of writing raw SQL by hand.
  *(Tip: set `echo=True` in `database.py` to watch the real SQL print live.)*
- **Persistence** — the difference between RAM (temporary) and disk (permanent).
- **Seeding & migrations** — how a fresh database gets its starter data.

## ➡️ Next step

**Connect the React frontend to this backend** so the portal's Login page works
for real and every screen shows live database data — completing the full-stack
loop (Frontend → API → Database).

---
*Educational material — SDLC Stage 8 (Database Development) demonstrated live.*
