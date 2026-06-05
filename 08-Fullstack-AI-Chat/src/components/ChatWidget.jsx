// ChatWidget.jsx (PHASE 2) — the floating 🤖 button students & trainers use to
// chat with the AI assistant. Unlike Phase 1 (which messaged a human admin),
// here the LLM replies automatically, so the reply appears right after sending.
import { useState, useEffect, useRef } from "react";
import { getMyChat, sendChat, getChatStatus, getRole } from "../services/api.js";

export default function ChatWidget() {
  const role = getRole();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null);
  const bottomRef = useRef(null);

  const load = () => getMyChat().then(setMessages).catch(() => {});

  useEffect(() => {
    if (!open) return;
    load();
    getChatStatus().then(setStatus).catch(() => {});
  }, [open]);

  // Header tag: shows the live provider (e.g. "gemini") or "demo" for the mock.
  const tag = status ? (status.mode === "live" ? status.provider : "demo") : "";

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async (e) => {
    e.preventDefault();
    if (!text.trim() || busy) return;
    setError(""); setBusy(true);
    try {
      await sendChat(text.trim()); // backend stores the message AND the AI reply
      setText("");
      await load();                // refresh → shows both the question and the answer
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  // Only students & trainers get the assistant widget (admins monitor via a page).
  if (role !== "student" && role !== "trainer") return null;

  return (
    <>
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} title="Ask the AI assistant">
          🤖
        </button>
      )}

      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span>🤖 AI Assistant{tag ? ` · ${tag}` : ""}</span>
            <button className="chat-close" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="chat-body">
            {messages.length === 0 && (
              <p className="chat-empty">Ask the AI anything about your courses, assignments, attendance or classes.</p>
            )}
            {messages.map((m) => (
              <div key={m.id} className={`chat-msg ${m.sender_role === "assistant" ? "from-admin" : "from-me"}`}>
                <div className="chat-bubble">{m.message}</div>
                <span className="chat-meta">{m.sender_role === "assistant" ? "🤖 AI Assistant" : "You"} · {m.created_at}</span>
              </div>
            ))}
            {busy && <div className="chat-msg from-admin"><div className="chat-bubble chat-typing">AI is typing…</div></div>}
            <div ref={bottomRef} />
          </div>

          {error && <p className="form-error" style={{ margin: ".5rem" }}>{error}</p>}

          <form className="chat-input" onSubmit={send}>
            <input
              type="text" value={text} placeholder="Ask the AI…"
              onChange={(e) => setText(e.target.value)} disabled={busy}
            />
            <button className="btn btn-sm" type="submit" disabled={busy}>Send</button>
          </form>
        </div>
      )}
    </>
  );
}
