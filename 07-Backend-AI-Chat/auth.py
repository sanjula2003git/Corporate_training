# =====================================================================
# auth.py  —  authentication + authorization (now backed by the DATABASE)
#
# Same idea as the in-memory version, but users are looked up from the real
# database table instead of a Python dictionary.
# =====================================================================
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from database import get_session
from models import UserDB

SECRET_KEY = "teknikoz-training-demo-secret-change-me"
ALGORITHM = "HS256"
TOKEN_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def make_username(session: Session, name: str) -> str:
    """Turn a person's name into a unique login (e.g. "Anita Sharma" -> "anita",
    then "anita2" if taken). This is how a freshly-added student/trainer gets a
    login automatically."""
    base = "".join(ch for ch in name.split(" ")[0].lower() if ch.isalnum()) or "user"
    candidate, n = base, 1
    while session.get(UserDB, candidate):
        n += 1
        candidate = f"{base}{n}"
    return candidate


def create_user_account(session: Session, name: str, role: str,
                        password: str, ref_id: str | None = None,
                        username: str | None = None) -> UserDB:
    """Create + persist a login. Used when an admin adds a student/trainer/admin."""
    username = username or make_username(session, name)
    user = UserDB(username=username, name=name, role=role,
                  password_hash=hash_password(password), ref_id=ref_id)
    session.add(user)
    return user


def authenticate(session: Session, username: str, password: str):
    user = session.get(UserDB, username)          # SELECT * FROM users WHERE username=?
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_token(user: UserDB) -> str:
    payload = {
        "sub": user.username,
        "role": user.role,
        "name": user.name,
        "ref_id": user.ref_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme),
                     session: Session = Depends(get_session)) -> UserDB:
    err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access pass. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise err
    user = session.get(UserDB, payload.get("sub"))
    if user is None:
        raise err
    return user


def require_role(*allowed_roles: str):
    def checker(user: UserDB = Depends(get_current_user)) -> UserDB:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role '{user.role}' is not allowed to do this.",
            )
        return user
    return checker
