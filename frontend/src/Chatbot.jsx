// Chatbot.jsx
import { useEffect, useRef, useState } from "react";

function getOrCreateSenderId() {
  const k = "rasa_uid";
  let v = localStorage.getItem(k);
  if (!v) {
    v = `web-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(k, v);
  }
  return v;
}

export default function Chatbot({ endpoint = "/chat/send", senderId }) {
  const uidRef = useRef(senderId || getOrCreateSenderId());

  const [messages, setMessages] = useState(() => [
    { id: 1, from: "bot", text: "¡Hola! Soy FITTER. ¿En qué te ayudo?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState("");
  const nextId = useRef(2);
  const scrollRef = useRef(null);
  const abortRef = useRef(null);

  // Autoscroll
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  // Limpieza al desmontar
  useEffect(() => () => abortRef.current?.abort(), []);

  const pushMessage = (msg) => {
    setMessages((prev) => [...prev, { id: nextId.current++, ...msg }]);
  };

  const normalizeBotPayloads = (data) => {
    if (!Array.isArray(data)) return [];
    return data.map((m) => ({
      id: nextId.current++,
      from: "bot",
      text: typeof m.text === "string" ? m.text : undefined,
      custom: m.custom || m.json_message || null,
      image: m.image || (m.attachment?.type === "image" ? m.attachment?.payload?.src : undefined),
      buttons: Array.isArray(m.buttons) ? m.buttons : undefined
    }));
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setErrorText("");
    pushMessage({ from: "user", text });
    setInput("");
    setLoading(true);

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: uidRef.current, message: text }),
        signal: controller.signal
      });

      if (!res.ok) {
        const t = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}${t ? `: ${t.slice(0, 160)}` : ""}`);
      }

      const data = await res.json();
      const botMsgs = normalizeBotPayloads(data);
      setMessages((prev) => botMsgs.length ? [...prev, ...botMsgs] : [...prev, { from: "bot", id: nextId.current++, text: "No recibí respuesta. ¿Puedes intentar de nuevo?" }]);
    } catch (e) {
      const msg = e?.name === "AbortError" ? "Solicitud cancelada." : "Error de conexión con el backend.";
      setErrorText(typeof e?.message === "string" ? e.message : msg);
      pushMessage({ from: "bot", text: "Error de conexión con el backend." });
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const Bubble = ({ children, from }) => (
    <span
      className="message"
      style={{
        display: "inline-block",
        padding: "8px 12px",
        borderRadius: from === "user" ? "16px 16px 0 16px" : "16px 16px 16px 0",
        background: from === "user" ? "#DCF8C6" : "#F1F0F0",
        maxWidth: "85%",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word"
      }}
    >
      {children}
    </span>
  );

  const renderMessageContent = (m) => {
    const hasRoutineLink = m?.custom?.type === "routine_link" && typeof m?.custom?.url === "string";
    const hasText = typeof m.text === "string" && m.text.length > 0;

    return (
      <>
        {hasText && <span>{m.text}</span>}
        {hasRoutineLink && (
          <>
            {hasText ? <br /> : null}
            <button
              type="button"
              onClick={() => window.open(m.custom.url, "_blank", "noopener,noreferrer")}
              style={{ marginTop: hasText ? 6 : 0, padding: "6px 12px", borderRadius: 8, border: "none", background: "#007bff", color: "white", cursor: "pointer" }}
              aria-label={m.custom.title || "Abrir rutina"}
            >
              {m.custom.title || "Abrir rutina"}
            </button>
          </>
        )}
        {m.image && (
          <>
            {(hasText || hasRoutineLink) ? <br /> : null}
            <img src={m.image} alt="Imagen enviada por el bot" style={{ display: "block", maxWidth: "100%", borderRadius: 8, marginTop: 6 }} loading="lazy" />
          </>
        )}
        {Array.isArray(m.buttons) && m.buttons.length > 0 && (
          <>
            {(hasText || hasRoutineLink || m.image) ? <br /> : null}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 6 }}>
              {m.buttons.map((b, idx) => (
                <button
                  key={`btn-${m.id}-${idx}`}
                  type="button"
                  onClick={() => {
                    const payload = b?.payload || b?.title || "";
                    if (payload) {
                      setInput(payload);
                      setTimeout(sendMessage, 0);
                    }
                  }}
                  style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #ddd", background: "#fff", cursor: "pointer" }}
                >
                  {b?.title || "Opción"}
                </button>
              ))}
            </div>
          </>
        )}
      </>
    );
  };

  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: 10,
        borderRadius: 8,
        width: "min(900px, 95%)",
        margin: "16px auto",
        background: "#fff",
        boxShadow: "0 1px 2px rgba(0,0,0,.06), 0 8px 24px rgba(0,0,0,.06)"
      }}
      role="region"
      aria-label="Chat con asistente FITTER"
    >
      <div ref={scrollRef} style={{ height: 360, overflowY: "auto", marginBottom: 10, padding: 6 }} aria-live="polite">
        {messages.map((m) => (
          <div key={m.id} style={{ textAlign: m.from === "user" ? "right" : "left", margin: "6px 0" }}>
            <Bubble from={m.from}>{renderMessageContent(m)}</Bubble>
          </div>
        ))}
        {loading && <div style={{ fontStyle: "italic", color: "#666", padding: "4px 6px" }}>Escribiendo…</div>}
      </div>

      {errorText && (
        <div style={{ color: "#b91c1c", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 8, padding: "6px 10px", marginBottom: 8 }} role="alert">
          {errorText}
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Escribe tu mensaje…"
          rows={1}
          style={{ flex: 1, padding: 10, borderRadius: 8, border: "1px solid #ccc", resize: "vertical", minHeight: 42, maxHeight: 160 }}
          aria-label="Cuadro de mensaje"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || input.trim().length === 0}
          style={{ padding: "10px 14px", borderRadius: 8, border: "none", background: loading ? "#9ca3af" : "#4CAF50", color: "white", cursor: loading ? "not-allowed" : "pointer" }}
          aria-busy={loading}
          aria-label="Enviar mensaje"
        >
          {loading ? "Enviando…" : "Enviar"}
        </button>
      </div>
    </div>
  );
}
