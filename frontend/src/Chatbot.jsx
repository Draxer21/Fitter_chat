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

      const data = await res.json(); // Rasa devuelve array de mensajes
      const botMsgs = (Array.isArray(data) ? data : []).map((m) => ({
        from: "bot",
        text: m.text ?? JSON.stringify(m)
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

  return (
    <div style={{ border: "1px solid #ccc", padding: 10, borderRadius: 8 }}>
      <div style={{ height: 320, overflowY: "auto", marginBottom: 10, padding: 6 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ textAlign: m.from === "user" ? "right" : "left", margin: "6px 0" }}>
            <span style={{
              display: "inline-block",
              padding: "8px 12px",
              borderRadius: 14,
              background: m.from === "user" ? "#DCF8C6" : "#F1F0F0"
            }}>
              {m.text}
            </span>
          </div>
        ))}
        {loading && <div style={{ fontStyle: "italic", color: "#666" }}>Escribiendo…</div>}
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
