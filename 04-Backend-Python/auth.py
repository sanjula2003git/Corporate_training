# =====================================================================
# auth.py  —  AUTHENTICATION (who are you?) + AUTHORIZATION (what may you do?)
#
# BUSINESS LEVEL:
#   - Login = showing your ID at the front desk.
#   - We check your password against the records.
#   - If correct, we hand you a TOKEN (a tamper-proof "access pass" / wristband).
#   - For every later action you show the pass instead of logging in again.
#   - ROLES (admin/trainer/student) decide which doors your pass can open.
#
# CODE LEVEL:
#   - bcrypt verifies the hashed password.
#   - PyJWT signs a token the server can later trust without a database lookup.
#   - FastAPI "dependencies" (get_current_user / require_role) guard endpoints.
# =====================================================================
import jwt                      # PyJWT
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import data

# In a real app this secret lives in an environment variable, never in code.
SECRET_KEY = "teknikoz-training-demo-secret-change-me"
ALGORITHM = "HS256"
TOKEN_MINUTES = 60   # the access pass expires after 1 hour

# Tells FastAPI where to get a token (also powers the "Authorize" button in /docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# ---- password checking ----
def verify_password(plain: str, password_hash: bytes) -> bool:
    # BUSINESS: does the typed password match the scrambled one on file?
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash)


def authenticate(username: str, password: str):
    user = data.users.get(username)
    if not user or not verify_password(password, user["password_hash"]):
        return None         # wrong username OR wrong password
    return user


# ---- token creation ----
def create_token(user: dict) -> str:
    # BUSINESS: print an access pass that says who they are and when it expires.
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "name": user["name"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---- read the token on protected requests ----
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access pass. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_error
    username = payload.get("sub")
    user = data.users.get(username)
    if user is None:
        raise credentials_error
    return user


# ---- role gate (AUTHORIZATION) ----
def require_role(*allowed_roles: str):
    # BUSINESS: "only these badge colours may open this door."
    # CODE: returns a dependency that checks the logged-in user's role.
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role '{user['role']}' is not allowed to do this.",
            )
        return user
    return checker
