# =====================================================================
# main.py  —  Backend + Database (SDLC Stage 8: Database Development)
#
# Same API as the previous backend, but data now lives in a REAL database
# (training.db) and SURVIVES server restarts. On startup we create the tables
# and seed them once.
#
# RUN IT:    python -m uvicorn main:app --reload
# THEN OPEN: http://127.0.0.1:8000/docs
# =====================================================================
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from database import init_db, get_session
from models import UserDB, StudentDB, TrainerDB, CourseDB
from auth import authenticate, create_token, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: build + seed the database.
    init_db()
    yield


app = FastAPI(
    title="ABC Learning — Training API (Phase 2: AI Chat)",
    description="Phase 2 backend: same portal, but the support chat is answered by an LLM (see llm.py).",
    version="3.0.0",
    lifespan=lifespan,
)

# Phase 2 runs on its OWN ports so it can run side-by-side with Phase 1:
#   backend :8001   ·   frontend :5273
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5273", "http://127.0.0.1:5273"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- AUTH ----
@app.post("/api/auth/login", tags=["Auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate(session, form.username, form.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")
    return {"access_token": create_token(user), "token_type": "bearer",
            "role": user.role, "name": user.name, "ref_id": user.ref_id}


@app.get("/api/auth/me", tags=["Auth"])
def me(user=Depends(get_current_user)):
    return {"username": user.username, "name": user.name,
            "role": user.role, "ref_id": user.ref_id}


# ---- DASHBOARD (counts come from the database now) ----
@app.get("/api/dashboard", tags=["Dashboard"])
def dashboard(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return {
        "totalStudents": len(session.exec(select(StudentDB)).all()),
        "totalTrainers": len(session.exec(select(TrainerDB)).all()),
        "totalCourses": len(session.exec(select(CourseDB)).all()),
        "avgAttendance": "87%",
        "recentActivities": [
            "New student Ravi Kumar enrolled in React Fundamentals.",
            "Trainer Anita Sharma assigned to Java Backend.",
            "Attendance saved for Python Basics (Batch 12).",
            "Certificate generated for Meera Nair.",
        ],
        "attendanceOverview": [
            {"day": "Mon", "value": 80}, {"day": "Tue", "value": 90},
            {"day": "Wed", "value": 85}, {"day": "Thu", "value": 92},
            {"day": "Fri", "value": 78},
        ],
    }


@app.get("/", tags=["Health"])
def root():
    return {"message": "Training API (with database) running. Open /docs to explore."}


# ---- plug in module routes ----
from routers import (students, trainers, courses, attendance, certificates,
                     reports, materials, assignments, submissions, classes,
                     admins, dashboards, chat)
app.include_router(students.router)
app.include_router(trainers.router)
app.include_router(courses.router)
app.include_router(attendance.router)
app.include_router(certificates.router)
app.include_router(reports.router)
app.include_router(materials.router)
app.include_router(assignments.router)
app.include_router(submissions.router)
app.include_router(classes.router)
app.include_router(admins.router)
app.include_router(dashboards.router)
app.include_router(chat.router)
