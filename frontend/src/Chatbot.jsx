// Chatbot.jsx
import { useState } from "react";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "¡Hola! Soy FITTER. ¿En qué te ayudo?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { from: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      // OJO: ruta relativa. CRA la enviará al proxy (Flask: 8080)
      const res = await fetch("/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: "web-user", message: text })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      // Rasa/Flask devuelve un array de mensajes (cada mensaje puede tener text y/o custom/json_message)
      const data = await res.json();

      const botMsgs = (Array.isArray(data) ? data : []).map((m) => ({
        from: "bot",
        text: typeof m.text === "string" ? m.text : undefined,
        // Normaliza: algunos canales usan "custom", otros "json_message"
        custom: m.custom || m.json_message || null
      }));

      setMessages((prev) => [...prev, ...botMsgs]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: "Error de conexión con el backend." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e) => e.key === "Enter" && sendMessage();

  const Bubble = ({ children, from }) => (
    <span
      style={{
        display: "inline-block",
        padding: "8px 12px",
        borderRadius: 14,
        background: from === "user" ? "#DCF8C6" : "#F1F0F0",
        maxWidth: "85%",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word"
      }}
    >
      {children}
    </span>
  );

  return (
    <div style={{ border: "1px solid #ccc", padding: 10, borderRadius: 8 }}>
      <div style={{ height: 320, overflowY: "auto", marginBottom: 10, padding: 6 }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              textAlign: m.from === "user" ? "right" : "left",
              margin: "6px 0"
            }}
          >
            <Bubble from={m.from}>
              {/* Caso: botón de rutina enviado por Rasa */}
              {m?.custom?.type === "routine_link" ? (
                <button
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: "none",
                    background: "#007bff",
                    color: "white",
                    cursor: "pointer"
                  }}
                  onClick={() =>
                    window.open(m.custom.url, "_blank", "noopener,noreferrer")
                  }
                >
                  {m.custom.title || "Abrir rutina"}
                </button>
              ) : (
                // Caso normal: texto
                (m.text ?? "")
              )}
            </Bubble>
          </div>
        ))}
        {loading && (
          <div style={{ fontStyle: "italic", color: "#666" }}>Escribiendo…</div>
        )}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Escribe tu mensaje…"
          style={{ flex: 1, padding: 10, borderRadius: 8, border: "1px solid #ccc" }}
        />
        <button onClick={sendMessage} style={{ padding: "10px 14px", borderRadius: 8 }}>
          Enviar
        </button>
      </div>
    </div>
  );
}
