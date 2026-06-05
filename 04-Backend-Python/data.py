# =====================================================================
# data.py  —  our in-memory "database" (seeded with the SAME data the
#             React frontend used in services/mockData.js)
#
# BUSINESS LEVEL: Think of this as the filing cabinet that holds all records
#   while the app is running. For this teaching phase we keep it in the
#   computer's memory (simple, zero setup). In the NEXT phase we replace this
#   with a real database (SQLite/PostgreSQL) so data survives restarts.
#
# CODE LEVEL: Plain Python lists/dicts act as tables. Swapping this file for a
#   real DB later means the rest of the app barely changes — good architecture.
# =====================================================================
import bcrypt


# --- helper: hash a plain password (one-way scramble) ---
def hash_password(plain: str) -> bytes:
    # BUSINESS: turns "admin123" into unreadable scramble. Even we can't reverse it.
    # CODE: bcrypt adds a random "salt" so identical passwords look different.
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())


# --- USERS (with roles) ---
# Three demo logins so you can show role separation in class.
# Passwords are stored HASHED, never as plain text.
users = {
    "admin": {
        "username": "admin",
        "name": "System Admin",
        "role": "admin",
        "password_hash": hash_password("admin123"),
    },
    "trainer": {
        "username": "trainer",
        "name": "Anita Sharma",
        "role": "trainer",
        "password_hash": hash_password("trainer123"),
    },
    "student": {
        "username": "student",
        "name": "Ravi Kumar",
        "role": "student",
        "password_hash": hash_password("student123"),
    },
}


# --- STUDENTS ---
students = [
    {"id": "STU-001", "name": "Ravi Kumar", "email": "ravi.kumar@example.com", "course": "React Fundamentals", "status": "Active"},
    {"id": "STU-002", "name": "Meera Nair", "email": "meera.nair@example.com", "course": "Python Basics", "status": "Active"},
    {"id": "STU-003", "name": "John Mathew", "email": "john.mathew@example.com", "course": "Java Backend", "status": "Inactive"},
    {"id": "STU-004", "name": "Aisha Khan", "email": "aisha.khan@example.com", "course": "React Fundamentals", "status": "Active"},
    {"id": "STU-005", "name": "David Lee", "email": "david.lee@example.com", "course": "Java Backend", "status": "Active"},
]

# --- TRAINERS ---
trainers = [
    {"id": "TRN-001", "name": "Anita Sharma", "expertise": "Java, Spring Boot", "courses": "Java Backend, Microservices"},
    {"id": "TRN-002", "name": "Suresh Rao", "expertise": "React, JavaScript", "courses": "React Fundamentals"},
    {"id": "TRN-003", "name": "Priya Menon", "expertise": "Python, Data Science", "courses": "Python Basics, ML 101"},
]

# --- COURSES ---
courses = [
    {"id": "CRS-001", "name": "React Fundamentals", "trainer": "Suresh Rao", "duration": "6 Weeks", "status": "Ongoing"},
    {"id": "CRS-002", "name": "Java Backend", "trainer": "Anita Sharma", "duration": "8 Weeks", "status": "Ongoing"},
    {"id": "CRS-003", "name": "Python Basics", "trainer": "Priya Menon", "duration": "4 Weeks", "status": "Completed"},
]

# --- CERTIFICATES ---
certificates = [
    {"student": "Meera Nair", "course": "Python Basics", "status": "Completed"},
    {"student": "Ravi Kumar", "course": "React Fundamentals", "status": "In Progress"},
    {"student": "John Mathew", "course": "Java Backend", "status": "Completed"},
]

# --- ATTENDANCE (filled in as it's saved) ---
attendance_records = []

recent_activities = [
    "New student Ravi Kumar enrolled in React Fundamentals.",
    "Trainer Anita Sharma assigned to Java Backend.",
    "Attendance saved for Python Basics (Batch 12).",
    "Certificate generated for Meera Nair.",
]


# --- helpers to generate the next ID ---
def next_id(items, prefix):
    return f"{prefix}-{str(len(items) + 1).zfill(3)}"
