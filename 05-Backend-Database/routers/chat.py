# routers/chat.py — support chat between students/trainers and the admins.
#
#   • A student/trainer has ONE thread (keyed by their username). They post a
#     message → it lands in the admin inbox.
#   • Any admin (the "superuser") sees every thread, opens one, and replies →
#     the reply appears in that student's/trainer's chat.
#
# No websockets — the frontend simply polls every few seconds, which is plenty
# for a teaching demo.
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import ChatMessageDB, ChatIn, UserDB
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


@router.post("", status_code=201)
def send_message(body: ChatIn, session: Session = Depends(get_session),
                 user=Depends(get_current_user)):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    if user.role == "admin":
        # An admin reply must say which thread (which student/trainer) it's for.
        if not body.to_user:
            raise HTTPException(status_code=400, detail="Admin reply needs a target user.")
        target = session.get(UserDB, body.to_user)
        if not target or target.role == "admin":
            raise HTTPException(status_code=404, detail="That user thread doesn't exist.")
        thread_user = body.to_user
    else:
        # Students/trainers always post into their own thread.
        thread_user = user.username

    msg = ChatMessageDB(thread_user=thread_user, sender_username=user.username,
                        sender_name=user.name, sender_role=user.role,
                        message=body.message.strip(), created_at=_now())
    session.add(msg); session.commit(); session.refresh(msg)
    return msg


@router.get("/me", response_model=list[ChatMessageDB])
def my_thread(session: Session = Depends(get_session), user=Depends(get_current_user)):
    """A student's/trainer's own conversation with the admins."""
    return session.exec(
        select(ChatMessageDB).where(ChatMessageDB.thread_user == user.username)
        .order_by(ChatMessageDB.id)
    ).all()


@router.get("/threads")
def list_threads(session: Session = Depends(get_session), user=Depends(require_role("admin"))):
    """Admin inbox: one entry per student/trainer who has messaged, with the
    last message and how many of their messages are awaiting a reply."""
    messages = session.exec(select(ChatMessageDB).order_by(ChatMessageDB.id)).all()
    threads = {}
    for m in messages:
        t = threads.setdefault(m.thread_user, {"messages": [], "last": None})
        t["messages"].append(m)
        t["last"] = m

    out = []
    for username, data in threads.items():
        owner = session.get(UserDB, username)
        msgs = data["messages"]
        # "Unanswered" = trailing run of user messages with no admin reply after.
        unanswered = 0
        for m in reversed(msgs):
            if m.sender_role == "admin":
                break
            unanswered += 1
        out.append({
            "thread_user": username,
            "name": owner.name if owner else username,
            "role": owner.role if owner else "?",
            "last_message": data["last"].message,
            "last_at": data["last"].created_at,
            "total": len(msgs),
            "unanswered": unanswered,
        })
    # Most recently active threads first.
    out.sort(key=lambda x: x["last_at"], reverse=True)
    return out


@router.get("/thread/{username}", response_model=list[ChatMessageDB])
def get_thread(username: str, session: Session = Depends(get_session),
               user=Depends(require_role("admin"))):
    """Full conversation for one student/trainer (admin view)."""
    return session.exec(
        select(ChatMessageDB).where(ChatMessageDB.thread_user == username)
        .order_by(ChatMessageDB.id)
    ).all()
