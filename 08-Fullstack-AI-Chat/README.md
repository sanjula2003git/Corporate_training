# Phase 2 — AI Chat (frontend) · `08-Fullstack-AI-Chat`

**ABC Learning Solutions — Training Management Portal (Phase 2)**

> ## 🤖 What makes this Phase 2
> This is a **separate copy** of Phase 1 (`06-Fullstack-Connected`). Everything
> is identical **except the support chat**:
>
> | | **Phase 1** (`06` + `05`) | **Phase 2** (`08` + `07`, this) |
> |--|---------------------------|----------------------------------|
> | Who answers the chat | a **human admin** (superuser) replies | an **AI assistant (Claude)** replies automatically |
> | Student/trainer widget | 💬 messages the admin inbox | 🤖 messages the LLM, gets an instant reply |
> | Admin chat page | inbox where the admin **replies** | **read-only** "AI Chat Logs" to monitor |
> | LLM key | n/a | reads `ANTHROPIC_API_KEY`; falls back to a **mock** reply with no key |
>
> **The two phases are kept fully separate and run on different ports**, so you
> can demo both at once. Phase 1 is untouched.
>
> | | Backend | Frontend |
> |--|---------|----------|
> | **Phase 1** | `05-Backend-Database` → :8000 | `06-Fullstack-Connected` → :5173 |
> | **Phase 2** | `07-Backend-AI-Chat` → :8001 | `08-Fullstack-AI-Chat` → :5273 |

## ▶️ Run Phase 2

```powershell
# Terminal 1 — Phase 2 backend (its own DB + port 8001)
cd 07-Backend-AI-Chat
python -m pip install -r requirements.txt        # first time
python -m uvicorn main:app --reload --port 8001

# Terminal 2 — Phase 2 frontend (port 5273)
cd 08-Fullstack-AI-Chat
npm install                                       # first time
npm run dev                                        # → http://localhost:5273
```

Log in as `ravi / student123`, click the 🤖 button, and ask something — the AI
replies right away. Log in as `admin` / `superuser` → **AI Chat Logs** to watch
the conversations (read-only). To use the **real** Claude model, copy
`07-Backend-AI-Chat/.env.example` to `.env` and set `ANTHROPIC_API_KEY`; without
it the assistant uses a built-in mock so the demo still works.

---

### (Below: the original full-stack/role-based notes, shared with Phase 1)

> The mock data layer has been swapped for **real API calls** to the Phase 2
> backend (`07-Backend-AI-Chat`). Every screen reads/writes the **live SQLite
> database** — completing the loop **Frontend → API → Database**.

---

## 👥 Three role-based portals (one app, one login screen)

After logging in, the **sidebar, dashboard and permissions change with your role** —
the backend enforces every rule, the UI just hides what isn't yours.

| | **Student** | **Trainer** | **Admin** (and any admin they create) |
|--|-------------|-------------|----------------------------------------|
| Dashboard | own attendance %, assignment % & marks | their students' progress + pending reviews | whole-org: every student/trainer, course progress |
| Course materials | **view** their course's materials | add / delete materials | add / delete materials |
| Assignments | **submit** work (text + link), see marks | **create**, review every student's work, **give marks** | same as trainer |
| Online classes | **join** via Google Meet link | **schedule** (paste Meet link) | schedule |
| Attendance | see own (read-only) | **mark** per-student attendance | mark + audit everyone |
| Students / Trainers / Courses | — | — | **add / update / delete** |
| Add another admin | — | — | ✅ |

> **Per-person logins:** when an admin adds a student or trainer, a login is
> **auto-created** (username from their first name, default password
> `student123` / `trainer123`) and shown on screen to share. Each person then
> signs in and sees only **their own** data.

---

## 🧠 The one big idea

| | `03-React-Version` (frontend only) | **`06-Fullstack-Connected` (this folder)** |
|--|-----------------------------------|--------------------------------------------|
| Where data comes from | hard-coded arrays in `mockData.js` | **HTTP calls to the backend** (`api.js`) |
| Login | accepts anything | **real auth** — only valid DB users get in |
| Add a student | lives in memory, gone on refresh | **saved to `training.db`**, survives refresh |
| Open it in two browsers | each has its own copy | both see the **same database** |
| The components (tables, cards) | **identical — not changed at all** | **identical — not changed at all** |

> 🎤 **Live class demo:** add a student in this React UI → open Swagger
> (`/docs`) or DB Browser → the **same new row is there**. Add one in Swagger →
> refresh React → **it appears in the UI**. One database, three windows.

## ▶️ How to run (TWO terminals)

**Terminal 1 — start the backend** (the database API):
```bash
cd 05-Backend-Database
python -m pip install -r requirements.txt      # first time only
python -m uvicorn main:app --reload            # → http://127.0.0.1:8000
```

**Terminal 2 — start this frontend:**
```bash
cd 06-Fullstack-Connected
npm install                                     # first time only
npm run dev                                      # → http://localhost:5173
```

Open **http://localhost:5173** and log in.

> ⚠️ The backend **must be running** or the UI will show connection errors.
> That's the lesson: they are **two separate programs** talking over HTTP.

## 🔑 Demo logins (real, from the database)

| Username | Password | Role | Sees |
|----------|----------|------|------|
| `admin` | `admin123` | Admin | full org dashboard + all management |
| `superuser` | `superuser123` | Admin (2nd) | identical powers — the second/super admin |
| `suresh` | `trainer123` | Trainer (React) | his students, his assignments to review |
| `anita` | `trainer123` | Trainer (Java) | her students, her assignments |
| `priya` | `trainer123` | Trainer (Python) | her students, her assignments |
| `ravi` | `student123` | Student (React) | own dashboard, materials, assignments, classes |
| `meera` / `john` / `aisha` / `david` | `student123` | Students | each sees only their own data |

> Try logging in as a **student** and you won't even see the Students/Trainers
> menu — and if you hit the API directly the backend returns **403 Forbidden**.
> Authorization is enforced on the *server*, not the browser.

## 🗂️ What changed from `03-React-Version` (the teaching diff)

**Only the data layer + a few pages changed. Every reusable component is byte-for-byte the same.**

| File | Change |
|------|--------|
| `src/services/api.js` | ⭐ **NEW** — replaces `mockData.js`; real `fetch()` calls + JWT token handling |
| `src/services/mockData.js` | ❌ **deleted** — no longer needed |
| `src/pages/Login.jsx` | now calls `POST /api/auth/login` and stores the token |
| `src/pages/Dashboard.jsx` | counts come from `GET /api/dashboard` |
| `src/pages/Students.jsx` | GET / POST / DELETE → real SELECT / INSERT / DELETE |
| `src/pages/Trainers.jsx` | same, against `/api/trainers` |
| `src/pages/Courses.jsx` | same, against `/api/courses` |
| `src/pages/Certificates.jsx` | list + server-validated "Generate" |
| `src/pages/Reports.jsx` | stats from `GET /api/reports` |
| `src/components/AttendanceForm.jsx` | loads students/courses from API, saves attendance |
| `src/components/Navbar.jsx` | shows the real logged-in user + 🟢 Live DB badge |
| `src/components/*` (tables, cards, panels) | **unchanged** — they only depend on props |

> 💡 This is the payoff of clean architecture promised in `03`'s README:
> *"Data source swap (mock → real API)? Change only the service layer;
> components are untouched because they depend on the service, not the source."*

### ➕ New in the role-based stage

| File | Purpose |
|------|---------|
| `src/components/Guards.jsx` | `RequireAuth` / `RequireRole` route protectors |
| `src/pages/Dashboard.jsx` | now a **role dispatcher** → Student / Trainer / Admin dashboard |
| `src/components/StudentDashboard / TrainerDashboard / AdminDashboard.jsx` | the three role views |
| `src/pages/Materials.jsx` | view (student) / manage (staff) course materials |
| `src/pages/Assignments.jsx` + `components/AssignmentReview.jsx` | submit (student) / create + grade (staff) |
| `src/pages/Classes.jsx` | join (student) / schedule Google Meet (staff) |
| `src/pages/MyProgress.jsx` | a student's own attendance + marks detail |
| `src/pages/Admins.jsx` | admin adds another admin; lists all accounts |
| `src/components/ProgressBar.jsx` | reusable % bar for attendance/progress |

Backend (`05-Backend-Database`) gained routers for `materials`, `assignments`,
`submissions`, `classes`, `admins`, and role `dashboards`, plus per-student
`attendance` and auto-created logins. The reusable tables/cards are still
unchanged — they only depend on props.

## 🔌 How the connection works (HTTP + token)

```
 Browser (React, :5173)                       Server (FastAPI, :8000)        Disk
 ─────────────────────                         ───────────────────────       ──────────
 Login form ──POST /api/auth/login──────────▶  check user in DB
            ◀──────── { access_token } ──────  issue JWT
 (token saved in localStorage)

 Students page ──GET /api/students────────────▶  SELECT * FROM students ───▶ training.db
   (Authorization: Bearer <token>)
              ◀──────── JSON rows ────────────  ◀──────────────────────────
 Add Student ──POST /api/students─────────────▶  INSERT INTO students ─────▶ training.db
```

- **CORS:** the backend explicitly allows `http://localhost:5173`, so the
  browser is permitted to call a different origin (port).
- **JWT token:** proves who you are on every protected request — the browser
  attaches it in the `Authorization` header automatically (see `api.js`).

## 🎓 Concepts this stage teaches

- **Client–server separation** — frontend and backend are independent programs
  on different ports; either can be viewed/tested alone.
- **REST in practice** — GET/POST/DELETE map to SELECT/INSERT/DELETE.
- **Authentication vs. authorization** — log in to get a token (authN);
  the server checks your role on each action (authZ).
- **Async UI** — `useEffect` loads data; the screen shows *Loading…* then real data.
- **End-to-end persistence** — a click in React lands as a row in SQLite and
  is visible from Swagger and DB Browser too.

---
*Educational material — the full-stack integration stage of the SDLC program.*
