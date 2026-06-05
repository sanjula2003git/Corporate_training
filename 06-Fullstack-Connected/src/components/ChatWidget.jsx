// ChatWidget.jsx — the floating 💬 button students & trainers use to message
// the superuser (admin). Opens a small chat panel; messages they send go to
// the admin inbox, and the admin's replies show up here. Polls every 4s.
import { useState, useEffect, useRef } from "react";
import { getMyChat, sendChat, getRole } from "../services/api.js";

export default function ChatWidget() {
  const role = getRole();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  const load = () => getMyChat().then(setMessages).catch(() => {});

  // Poll for new replies while the panel is open.
  useEffect(() => {
    if (!open) return;
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [open]);

  // Auto-scroll to the newest message.
  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setError("");
    try {
      await sendChat(text.trim());
      setText("");
      load();
    } catch (err) { setError(err.message); }
  };

  // Only students & trainers get the support widget (admins use the inbox page).
  if (role !== "student" && role !== "trainer") return null;

  return (
    <>
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} title="Message support">
          💬
        </button>
      )}

      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span>💬 Support · Admin</span>
            <button className="chat-close" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="chat-body">
            {messages.length === 0 && (
              <p className="chat-empty">Ask the admin anything — they'll reply here.</p>
            )}
            {messages.map((m) => (
              <div key={m.id} className={`chat-msg ${m.sender_role === "admin" ? "from-admin" : "from-me"}`}>
                <div className="chat-bubble">{m.message}</div>
                <span className="chat-meta">{m.sender_role === "admin" ? `${m.sender_name} (admin)` : "You"} · {m.created_at}</span>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {error && <p className="form-error" style={{ margin: ".5rem" }}>{error}</p>}

          <form className="chat-input" onSubmit={send}>
            <input
              type="text" value={text} placeholder="Type a message…"
              onChange={(e) => setText(e.target.value)}
            />
            <button className="btn btn-sm" type="submit">Send</button>
          </form>
        </div>
      )}
    </>
  );
}
