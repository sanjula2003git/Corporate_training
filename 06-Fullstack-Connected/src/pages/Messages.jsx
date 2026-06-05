// Messages.jsx — the admin (superuser) inbox. Left: every student/trainer who
// has messaged, newest first, with an "unanswered" badge. Right: the selected
// conversation + a reply box. Replies land in that person's chat widget.
import { useState, useEffect, useRef } from "react";
import { getChatThreads, getChatThread, sendChat } from "../services/api.js";

export default function Messages() {
  const [threads, setThreads] = useState([]);
  const [active, setActive] = useState(null);     // thread_user currently open
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  const loadThreads = () => getChatThreads().then(setThreads).catch((e) => setError(e.message));
  const loadActive = () => { if (active) getChatThread(active).then(setMessages).catch(() => {}); };

  // Poll the inbox + the open conversation.
  useEffect(() => {
    loadThreads();
    const t = setInterval(loadThreads, 5000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    loadActive();
    if (!active) return;
    const t = setInterval(loadActive, 4000);
    return () => clearInterval(t);
  }, [active]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const reply = async (e) => {
    e.preventDefault();
    if (!text.trim() || !active) return;
    setError("");
    try {
      await sendChat(text.trim(), active);
      setText("");
      loadActive();
      loadThreads();
    } catch (err) { setError(err.message); }
  };

  const activeThread = threads.find((t) => t.thread_user === active);

  return (
    <>
      <div className="page-head"><h2>Messages</h2></div>
      {error && <p className="form-error">{error}</p>}

      <div className="inbox">
        {/* Thread list */}
        <div className="inbox-list panel">
          <h2>Inbox</h2>
          {threads.length === 0 && <p className="muted-line">No messages yet.</p>}
          {threads.map((t) => (
            <button
              key={t.thread_user}
              className={`inbox-item ${active === t.thread_user ? "active" : ""}`}
              onClick={() => setActive(t.thread_user)}
            >
              <div className="inbox-item-top">
                <strong>{t.name}</strong>
                <span className={`badge ${t.role === "trainer" ? "badge-warning" : "badge-muted"}`}>{t.role}</span>
              </div>
              <div className="inbox-preview">{t.last_message}</div>
              <div className="inbox-item-bottom">
                <span className="muted-line">{t.last_at}</span>
                {t.unanswered > 0 && <span className="badge badge-danger-soft">{t.unanswered} new</span>}
              </div>
            </button>
          ))}
        </div>

        {/* Conversation */}
        <div className="inbox-convo panel">
          {!active && <p className="muted-line">Select a conversation to read and reply.</p>}
          {active && (
            <>
              <h2>{activeThread?.name} <span className="muted-line">· {activeThread?.role}</span></h2>
              <div className="chat-body chat-body-tall">
                {messages.map((m) => (
                  <div key={m.id} className={`chat-msg ${m.sender_role === "admin" ? "from-me" : "from-admin"}`}>
                    <div className="chat-bubble">{m.message}</div>
                    <span className="chat-meta">{m.sender_role === "admin" ? `${m.sender_name} (you)` : m.sender_name} · {m.created_at}</span>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
              <form className="chat-input" onSubmit={reply}>
                <input type="text" value={text} placeholder="Type your reply…" onChange={(e) => setText(e.target.value)} />
                <button className="btn btn-sm" type="submit">Reply</button>
              </form>
            </>
          )}
        </div>
      </div>
    </>
  );
}
