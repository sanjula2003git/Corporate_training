# =====================================================================
# main.py  —  the heart of the backend (SDLC Stage 7: Backend Development)
#
# BUSINESS LEVEL: This is the "kitchen + front desk" of the restaurant.
#   The React app (dining room) sends orders here; this file routes each order
#   to the right station (students, trainers, courses...) and sends food back.
#   The front desk also checks IDs at login and hands out access passes.
#
# CODE LEVEL: Creates the FastAPI app, enables CORS (so the browser frontend
#   may talk to us), wires in every router, and defines /login + /dashboard.
#
# RUN IT:   uvicorn main:app --reload
# THEN OPEN: http://127.0.0.1:8000/docs   <-- interactive, clickable API page
# =====================================================================
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

import data
from models import Token
from auth import authenticate, create_token, get_current_user, require_role
from routers import students, trainers, courses, attendance, certificates, reports

app = FastAPI(
    title="ABC Learning — Training Management API",
    description="Backend for the Corporate Training Portal. Educational SDLC demo.",
    version="1.0.0",
)

# ---- CORS ----
# BUSINESS: permission slip letting the website (on its own address) call this
#   server (on a different address). Without it, browsers block the request.
# CODE: allow the React dev server origins. Tighten this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:5174",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- AUTH: login ----
@app.post("/api/auth/login", response_model=Token, tags=["Auth"])
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Login page calls this. Returns an access token (the 'pass') on success."""
    user = authenticate(form.username, form.password)
    if not user:
        # BUSINESS: wrong ID — front desk refuses entry.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_token(user)
    return {"access_token": token, "token_type": "bearer",
            "role": user["role"], "name": user["name"]}


# ---- AUTH: who am I (uses the token) ----
@app.get("/api/auth/me", tags=["Auth"])
def me(user=Depends(get_current_user)):
    return {"username": user["username"], "name": user["name"], "role": user["role"]}


# ---- DASHBOARD ----
@app.get("/api/dashboard", tags=["Dashboard"])
def dashboard(user=Depends(get_current_user)):
    return {
        "totalStudents": len(data.students),
        "totalTrainers": len(data.trainers),
        "totalCourses": len(data.courses),
        "avgAttendance": "87%",
        "recentActivities": data.recent_activities,
        "attendanceOverview": [
            {"day": "Mon", "value": 80}, {"day": "Tue", "value": 90},
            {"day": "Wed", "value": 85}, {"day": "Thu", "value": 92},
            {"day": "Fri", "value": 78},
        ],
    }


# ---- a friendly root so visiting / isn't a 404 ----
@app.get("/", tags=["Health"])
def root():
    return {"message": "Training Management API is running. Open /docs to explore."}


# ---- plug in every module's routes ----
app.include_router(students.router)
app.include_router(trainers.router)
app.include_router(courses.router)
app.include_router(attendance.router)
app.include_router(certificates.router)
app.include_router(reports.router)
