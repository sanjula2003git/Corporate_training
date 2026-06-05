# =====================================================================
# llm.py  —  the AI assistant brain (PHASE 2 only).
#
# In Phase 1 (05/06) a human admin answered the support chat. In Phase 2 the
# chat goes to an LLM and the LLM answers automatically.
#
# PROVIDER (picked automatically, in this order):
#   1. GEMINI_API_KEY set      → Google Gemini (FREE tier — recommended).
#                                 Get a key at https://aistudio.google.com/apikey
#   2. ANTHROPIC_API_KEY set   → Anthropic Claude (paid).
#   3. neither                 → built-in MOCK reply, so the demo runs with no key.
#
# Gemini is called over plain REST (urllib) so NO extra Python package is
# needed — just the key.
# =====================================================================
import os
import json
import urllib.request
import urllib.error

# Optional .env loading (so a key in .env "just works" once you add it).
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Anthropic SDK is optional — only imported if you choose that provider.
try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None

GEMINI_MODEL = "gemini-2.0-flash"       # fast + free-tier friendly
CLAUDE_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are the AI learning assistant for ABC Learning Solutions, a corporate "
    "training company. You help students and trainers with questions about their "
    "courses (React Fundamentals, Java Backend, Python Basics), assignments, "
    "attendance, online classes, certificates and marks. Be concise, friendly and "
    "practical. If a question needs data you don't have, explain where in the "
    "portal to find it (e.g. 'My Assignments', 'My Progress', 'Online Classes'). "
    "Never invent specific marks or attendance numbers."
)


def provider() -> str:
    """Which backend will answer: 'gemini', 'anthropic', or 'mock'."""
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY") and Anthropic is not None:
        return "anthropic"
    return "mock"


def is_live() -> bool:
    return provider() != "mock"


def generate_reply(user_role: str, user_name: str, history: list, message: str) -> str:
    """Return the assistant's reply. `history` is the full thread (oldest first)
    and already ENDS with the user's latest message."""
    p = provider()
    try:
        if p == "gemini":
            return _gemini_reply(history)
        if p == "anthropic":
            return _claude_reply(history)
    except Exception as e:
        # Never break the chat — degrade to the mock with a small note.
        return _mock_reply(user_name, message) + f"\n\n_(live AI unavailable: {e})_"
    return _mock_reply(user_name, message)


# ---------------- Google Gemini (REST, free tier) ----------------
def _gemini_reply(history: list) -> str:
    key = os.environ["GEMINI_API_KEY"]
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={key}")
    contents = [
        {"role": "model" if h.sender_role == "assistant" else "user",
         "parts": [{"text": h.message}]}
        for h in history
    ]
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 400, "temperature": 0.4},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:200]
        raise RuntimeError(f"Gemini HTTP {e.code}: {detail}")
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


# ---------------- Anthropic Claude (paid) ----------------
def _claude_reply(history: list) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [
        {"role": "assistant" if h.sender_role == "assistant" else "user",
         "content": h.message}
        for h in history
    ]
    resp = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=400,
        system=[{"type": "text", "text": SYSTEM_PROMPT,
                 "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


# ---------------- MOCK (no API key needed) ----------------
def _mock_reply(user_name: str, message: str) -> str:
    """A lightweight keyword-based stand-in for the LLM. Good enough to show the
    end-to-end flow until a real key (Gemini/Anthropic) is configured."""
    m = message.lower()
    first = (user_name or "there").split(" ")[0]

    def has(*words):
        return any(w in m for w in words)

    if has("assignment", "homework", "submit", "submission"):
        reply = ("Open **My Assignments** to see each task, its due date and max "
                 "marks. Type your answer (and an optional link) and hit Submit. "
                 "Once your trainer grades it, the marks and feedback appear there.")
    elif has("attendance", "present", "absent"):
        reply = ("You can track attendance under **My Progress** — it shows every "
                 "class you attended and your overall percentage.")
    elif has("class", "meet", "live", "join", "schedule"):
        reply = ("Upcoming live classes are under **Online Classes**. Click "
                 "**Join Class** to open the Google Meet link at the scheduled time.")
    elif has("certificate", "certified"):
        reply = ("Certificates are issued once a course is marked **Completed**. "
                 "Your trainer/admin generates it from the Certificates page.")
    elif has("marks", "grade", "score", "result"):
        reply = ("Your marks and the trainer's feedback show up in **My Progress** "
                 "and on each graded assignment.")
    elif has("password", "login", "sign in", "reset"):
        reply = ("For login or password help, an admin can reset your account. "
                 "Your username was shared when your profile was created.")
    elif has("material", "notes", "resource", "video", "docs"):
        reply = ("Course materials (docs and videos) are under **Course "
                 "Materials** — only your enrolled course's resources are shown.")
    elif has("hi", "hello", "hey", "good morning", "good evening"):
        reply = f"Hi {first}! I'm your AI learning assistant. Ask me about your courses, assignments, attendance, classes or certificates."
    else:
        reply = ("Thanks for your message! I'm your AI learning assistant. I can "
                 "help with courses, assignments, attendance, online classes, "
                 "marks and certificates — could you tell me a bit more about what "
                 "you need?")
    return reply
