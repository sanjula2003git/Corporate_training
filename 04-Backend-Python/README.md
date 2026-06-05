# Backend (Python + FastAPI) — SDLC Stage 7: Backend Development

**ABC Learning Solutions — Training Management Portal**

> This is the **backend** that brings the frontend to life. It adds the three
> things a frontend alone can never do: a real **server/API**, real
> **authentication** (login that actually checks), and **roles** (Admin /
> Trainer / Student see and do different things).

---

## 🧠 The big idea (for any audience)

| Part | Restaurant analogy | In this project |
|------|--------------------|-----------------|
| Frontend | Dining room | The HTML/CSS/React portal |
| **Backend** | **Kitchen + front desk** | **This FastAPI app** |
| API | Waiter carrying orders | The `/api/...` endpoints |
| Auth | ID badge + access pass | Login → JWT token |
| Database | Pantry (next phase) | In-memory for now |

Remember how **any password worked** on the frontend Login page? That's because
the frontend had no one to ask. **This backend is who it asks.**

## 📁 Folder structure

```
04-Backend-Python/
├── main.py            # the app: CORS, login, dashboard, wires in routers
├── auth.py            # authentication (JWT) + authorization (roles)
├── data.py            # in-memory "database" (seeded, + hashed passwords)
├── models.py          # data shapes (Pydantic) + automatic validation
├── requirements.txt   # dependencies
└── routers/           # one file per module (mirrors the frontend screens)
    ├── students.py
    ├── trainers.py
    ├── courses.py
    ├── attendance.py
    ├── certificates.py
    └── reports.py
```

## ▶️ How to run

```bash
cd 04-Backend-Python
python -m pip install -r requirements.txt      # first time only
python -m uvicorn main:app --reload
```

Then open the **interactive API page** (great for class demos):

### 👉 http://127.0.0.1:8000/docs

On that page anyone — even non-coders — can click **"Try it out"** to call the
API and see live results. Use the green **"Authorize 🔓"** button to log in,
then the protected endpoints unlock.

## 🔑 Demo logins (show role separation in class)

| Username | Password | Role | Can do |
|----------|----------|------|--------|
| `admin` | `admin123` | Admin | Everything (incl. delete) |
| `trainer` | `trainer123` | Trainer | View, add students, mark attendance, generate certificates |
| `student` | `student123` | Student | View only |

> Passwords are stored **hashed** (bcrypt), never as plain text.

## 🔌 API endpoints

| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| POST | `/api/auth/login` | anyone | Log in → get token |
| GET | `/api/auth/me` | logged-in | Who am I? |
| GET | `/api/dashboard` | logged-in | Dashboard cards + activity |
| GET/POST/PUT/DELETE | `/api/students` | view: all · add/edit: admin+trainer · delete: admin | Student CRUD |
| GET/POST/PUT/DELETE | `/api/trainers` | view: all · changes: admin | Trainer CRUD |
| GET/POST/PUT/DELETE | `/api/courses` | view: all · changes: admin | Course CRUD |
| GET/POST | `/api/attendance` | mark: admin+trainer | Attendance |
| GET | `/api/certificates` | logged-in | List certificates |
| POST | `/api/certificates/generate` | admin+trainer | Issue certificate (Completed only) |
| GET | `/api/reports` | admin+trainer | Management stats |

## 🎓 Concepts this stage teaches

- **What an API is** — the frontend asks, the backend answers (HTTP + JSON).
- **REST** — predictable verbs: GET (read), POST (create), PUT (update), DELETE.
- **Authentication** — login verifies identity, returns a signed **JWT** token.
- **Authorization (roles)** — the same token decides *what you're allowed to do*.
- **Password hashing** — bcrypt; even we can't read the real password.
- **CORS** — the permission that lets the browser frontend call this server.
- **Validation** — Pydantic rejects badly-shaped data automatically.
- **Separation of concerns** — routers / auth / data / models in separate files
  (the backend mirror of the React components/pages/services split).

## ➡️ Next phases (the teaching arc continues)

- **B2 — Real database:** replace `data.py` (memory) with SQLite/PostgreSQL so
  data survives restarts. Only `data.py` changes — everything else stays.
- **B3 — Connect the React frontend:** point the app's `services/mockData.js`
  `fetchData()` at `http://127.0.0.1:8000/api/...` so the UI uses live data and
  the Login page finally works for real.

---
*Educational material — SDLC Stages 7 (Backend) & 8 (Database) demonstrated live.*
