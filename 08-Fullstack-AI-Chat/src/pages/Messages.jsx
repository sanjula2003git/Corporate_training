// Messages.jsx (PHASE 2) — admin MONITOR of AI conversations (read-only).
// The AI answers students/trainers automatically; admins don't reply here, they
// just review what people asked and how the assistant responded. Left: every
// person who used the assistant. Right: the full transcript.
import { useState, useEffect, useRef } from "react";
import { getChatThreads, getChatThread } from "../services/api.js";

export default function Messages() {
  const [threads, setThreads] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  const loadThreads = () => getChatThreads().then(setThreads).catch((e) => setError(e.message));
  const loadActive = () => { if (active) getChatThread(active).then(setMessages).catch(() => {}); };

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

  const activeThread = threads.find((t) => t.thread_user === active);

  return (
    <>
      <div className="page-head">
        <h2>AI Chat Logs</h2>
        <span className="badge badge-muted">read-only · the AI answers automatically</span>
      </div>
      {error && <p className="form-error">{error}</p>}

      <div className="inbox">
        <div className="inbox-list panel">
          <h2>Conversations</h2>
          {threads.length === 0 && <p className="muted-line">No one has used the assistant yet.</p>}
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
                <span className="muted-line">{t.total} msgs</span>
              </div>
            </button>
          ))}
        </div>

        <div className="inbox-convo panel">
          {!active && <p className="muted-line">Select a conversation to read the transcript.</p>}
          {active && (
            <>
              <h2>{activeThread?.name} <span className="muted-line">· {activeThread?.role}</span></h2>
              <div className="chat-body chat-body-tall">
                {messages.map((m) => (
                  <div key={m.id} className={`chat-msg ${m.sender_role === "assistant" ? "from-admin" : "from-me"}`}>
                    <div className="chat-bubble">{m.message}</div>
                    <span className="chat-meta">{m.sender_role === "assistant" ? "🤖 AI Assistant" : m.sender_name} · {m.created_at}</span>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
