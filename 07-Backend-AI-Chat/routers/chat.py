# routers/chat.py — AI ASSISTANT chat (PHASE 2).
#
# Difference from Phase 1: the message does NOT wait for a human admin. When a
# student/trainer sends a message, the backend immediately asks the LLM
# (see llm.py) and stores its reply in the same thread. Admins can still READ
# every conversation (to monitor), but they don't reply — the AI does.
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import ChatMessageDB, ChatIn, UserDB
from auth import get_current_user, require_role
from llm import generate_reply, is_live, provider

router = APIRouter(prefix="/api/chat", tags=["Chat (AI)"])

AI_USERNAME = "ai-assistant"
AI_NAME = "AI Assistant"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


@router.get("/status")
def chat_status(user=Depends(get_current_user)):
    """Tells the UI whether replies are from a real LLM (and which) or the mock."""
    return {"mode": "live" if is_live() else "mock", "provider": provider()}


@router.post("", status_code=201)
def send_message(body: ChatIn, session: Session = Depends(get_session),
                 user=Depends(get_current_user)):
    if user.role == "admin":
        raise HTTPException(status_code=400,
                            detail="In Phase 2 the AI assistant answers automatically — admins monitor only.")
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    thread_user = user.username

    # 1) store the student's/trainer's message
    user_msg = ChatMessageDB(thread_user=thread_user, sender_username=user.username,
                             sender_name=user.name, sender_role=user.role,
                             message=body.message.strip(), created_at=_now())
    session.add(user_msg); session.commit(); session.refresh(user_msg)
    user_payload = user_msg.model_dump()   # capture before the next commit expires it

    # 2) ask the LLM, using the full thread as context
    history = session.exec(
        select(ChatMessageDB).where(ChatMessageDB.thread_user == thread_user)
        .order_by(ChatMessageDB.id)
    ).all()
    reply_text = generate_reply(user.role, user.name, history, body.message.strip())

    # 3) store the AI's reply in the same thread
    ai_msg = ChatMessageDB(thread_user=thread_user, sender_username=AI_USERNAME,
                           sender_name=AI_NAME, sender_role="assistant",
                           message=reply_text, created_at=_now())
    session.add(ai_msg); session.commit(); session.refresh(ai_msg)
    return {"message": user_payload, "reply": ai_msg.model_dump()}


@router.get("/me", response_model=list[ChatMessageDB])
def my_thread(session: Session = Depends(get_session), user=Depends(get_current_user)):
    """A student's/trainer's own conversation with the AI assistant."""
    return session.exec(
        select(ChatMessageDB).where(ChatMessageDB.thread_user == user.username)
        .order_by(ChatMessageDB.id)
    ).all()


# ---- Admin MONITORING (read-only): see what people are asking the AI ----
@router.get("/threads")
def list_threads(session: Session = Depends(get_session), user=Depends(require_role("admin"))):
    messages = session.exec(select(ChatMessageDB).order_by(ChatMessageDB.id)).all()
    threads = {}
    for msg in messages:
        t = threads.setdefault(msg.thread_user, {"messages": [], "last": None})
        t["messages"].append(msg)
        t["last"] = msg

    out = []
    for username, data in threads.items():
        owner = session.get(UserDB, username)
        out.append({
            "thread_user": username,
            "name": owner.name if owner else username,
            "role": owner.role if owner else "?",
            "last_message": data["last"].message,
            "last_at": data["last"].created_at,
            "total": len(data["messages"]),
        })
    out.sort(key=lambda x: x["last_at"], reverse=True)
    return out


@router.get("/thread/{username}", response_model=list[ChatMessageDB])
def get_thread(username: str, session: Session = Depends(get_session),
               user=Depends(require_role("admin"))):
    return session.exec(
        select(ChatMessageDB).where(ChatMessageDB.thread_user == username)
        .order_by(ChatMessageDB.id)
    ).all()
