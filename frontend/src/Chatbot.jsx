// Chatbot.jsx
import { useEffect, useRef, useState } from "react";
import "./styles/Chatbot.css";

const SENDER_STORAGE_KEY = "rasa_uid";

function createSenderId() {
  return `web-${Math.random().toString(36).slice(2, 10)}`;
}

function getOrCreateSenderId(forceNew = false) {
  let v = !forceNew ? localStorage.getItem(SENDER_STORAGE_KEY) : null;
  if (!v) {
    v = createSenderId();
    localStorage.setItem(SENDER_STORAGE_KEY, v);
  }
  return v;
}

export default function Chatbot({ endpoint = "/chat/send", senderId, onNewMessage, initialMessages = [] }) {
  const uidRef = useRef(senderId || getOrCreateSenderId());

  const [messages, setMessages] = useState(() => {
    // Si hay mensajes iniciales, usarlos; si no, mostrar el mensaje de bienvenida
    if (initialMessages && initialMessages.length > 0) {
      return initialMessages.map((msg, idx) => ({
        id: idx + 1,
        from: msg.from || "bot",
        text: msg.text
      }));
    }
    return [{ id: 1, from: "bot", text: "¡Hola! Soy FITTER. ¿En qué te ayudo?" }];
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState("");
  const [expandedCards, setExpandedCards] = useState({});
  const nextId = useRef(initialMessages.length > 0 ? initialMessages.length + 1 : 2);
  const scrollRef = useRef(null);
  const abortRef = useRef(null);

  // Actualizar mensajes cuando cambian los initialMessages
  useEffect(() => {
    if (initialMessages && initialMessages.length > 0) {
      setMessages(initialMessages.map((msg, idx) => ({
        id: idx + 1,
        from: msg.from || "bot",
        text: msg.text
      })));
      nextId.current = initialMessages.length + 1;
    } else {
      setMessages([{ id: 1, from: "bot", text: "¡Hola! Soy FITTER. ¿En qué te ayudo?" }]);
      nextId.current = 2;
    }
  }, [initialMessages]);

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

  const sendToBackend = async (text, retrying = false) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ sender: uidRef.current, message: text }),
      signal: controller.signal
    });

    if (res.status === 401 && !retrying) {
      // Sender quedó asociado a otro usuario; regeneramos y reintentamos una vez
      localStorage.removeItem(SENDER_STORAGE_KEY);
      uidRef.current = getOrCreateSenderId(true);
      return sendToBackend(text, true);
    }

    if (!res.ok) {
      const t = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status}${t ? `: ${t.slice(0, 160)}` : ""}`);
    }

    const data = await res.json();
    const botMsgs = normalizeBotPayloads(data);
    setMessages((prev) =>
      botMsgs.length
        ? [...prev, ...botMsgs]
        : [...prev, { from: "bot", id: nextId.current++, text: "No recibí respuesta. ¿Puedes intentar de nuevo?" }]
    );
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setErrorText("");
    pushMessage({ from: "user", text });
    setInput("");
    setLoading(true);

    if (onNewMessage && typeof onNewMessage === "function") {
      onNewMessage(text);
    }

    try {
      await sendToBackend(text);
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

  const toggleCard = (key) => {
    setExpandedCards((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const downloadRoutine = async (routineDetail, format) => {
    try {
      const response = await fetch("/notifications/download-routine", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          format: format,
          routine_data: routineDetail
        })
      });

      if (!response.ok) {
        throw new Error(`Error al descargar: ${response.status}`);
      }

      // Descargar el archivo
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${routineDetail.routine_id || "rutina"}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error al descargar rutina:", error);
      alert(`No se pudo descargar la rutina en formato ${format.toUpperCase()}. Intenta de nuevo.`);
    }
  };

  const Bubble = ({ children, from }) => (
    <div className={`message-bubble ${from === "user" ? "user-bubble" : "bot-bubble"}`}>
      {children}
    </div>
  );

  const renderMessageContent = (m) => {
    const hasRoutineLink = m?.custom?.type === "routine_link" && typeof m?.custom?.url === "string";
    const routineDetail = m?.custom?.type === "routine_detail" ? m.custom : null;
    const routineKey = routineDetail ? `routine-${m.id}` : null;
    const isRoutineExpanded = routineKey ? !!expandedCards[routineKey] : false;
    const dietPlan = m?.custom?.type === "diet_plan" ? m.custom : null;
    const dietSummary = dietPlan?.summary || {};
    const dietMeals = Array.isArray(dietPlan?.meals) ? dietPlan.meals : [];
    const dietAdjustments = Array.isArray(dietSummary.health_adjustments) ? dietSummary.health_adjustments : [];
    const allergenHits = Array.isArray(dietSummary.allergen_hits) ? dietSummary.allergen_hits : [];
    const dietKey = dietPlan ? `diet-${m.id}` : null;
    const isDietExpanded = dietKey ? !!expandedCards[dietKey] : false;
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
              className="message-action-button message-primary-button"
              style={{ marginTop: hasText ? 6 : 0 }}
              aria-label={m.custom.title || "Abrir rutina"}
            >
              {m.custom.title || "Abrir rutina"}
            </button>
          </>
        )}
        {routineDetail && (
          <>
            {(hasText || hasRoutineLink) ? <br /> : null}
            <button
              type="button"
              onClick={() => routineKey && toggleCard(routineKey)}
              className="message-action-button message-routine-button"
              style={{ marginTop: hasText || hasRoutineLink ? 6 : 0 }}
            >
              {isRoutineExpanded ? "Ocultar rutina" : "Ver rutina aqui"}
            </button>
            {isRoutineExpanded && (
              <div className="routine-card">
                {routineDetail.header && <p style={{ margin: 0, fontWeight: 600 }}>{routineDetail.header}</p>}
                <div style={{ fontSize: "0.85rem", marginTop: 6, display: "grid", gap: 4 }}>
                  <span><strong>Tiempo:</strong> {routineDetail.summary?.tiempo_min ?? "-"} min</span>
                  <span><strong>Ejercicios:</strong> {routineDetail.summary?.ejercicios ?? "-"}</span>
                  <span><strong>Equipo:</strong> {routineDetail.summary?.equipamiento ?? "-"}</span>
                  <span><strong>Objetivo:</strong> {routineDetail.summary?.objetivo ?? "-"}</span>
                  <span><strong>Nivel:</strong> {routineDetail.summary?.nivel ?? "-"}</span>
                </div>
                
                {/* Botones de descarga */}
                <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => downloadRoutine(routineDetail, "pdf")}
                    className="download-button download-pdf"
                    title="Descargar en PDF"
                  >
                    📄 Descargar PDF
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadRoutine(routineDetail, "docx")}
                    className="download-button download-docx"
                    title="Descargar en Word"
                  >
                    📝 Descargar Word
                  </button>
                  <button
                    type="button"
                    onClick={() => sendRoutineByEmail(routineDetail)}
                    className="download-button download-send"
                    title="Enviar por correo"
                  >
                    📤 Enviar por correo
                  </button>
                </div>
                
                {Array.isArray(routineDetail.summary?.health_notes) && routineDetail.summary.health_notes.length > 0 && (
                  <div className="health-warning">
                    <strong>Precauciones:</strong>
                    <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                      {routineDetail.summary.health_notes.map((note, idx) => (
                        <li key={`routine-health-${m.id}-${idx}`}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {Array.isArray(routineDetail.summary?.allergies) && routineDetail.summary.allergies.length > 0 && (
                  <p style={{ marginTop: 6, fontSize: "0.8rem", color: "#6b7280" }}>
                    Alergias registradas: {routineDetail.summary.allergies.join(", ")}
                  </p>
                )}
                {routineDetail.fallback_notice && (
                  <p style={{ marginTop: 6, fontSize: "0.8rem", color: "#92400e" }}>
                    {routineDetail.fallback_notice}
                  </p>
                )}
                {Array.isArray(routineDetail.exercises) && routineDetail.exercises.length > 0 && (
                  <ol style={{ marginTop: 10, paddingLeft: 18, display: "grid", gap: 6 }}>
                    {routineDetail.exercises.map((ex) => (
                      <li key={`${m.id}-${ex?.orden ?? ex?.nombre}`} style={{ fontSize: "0.85rem" }}>
                        <strong>{ex?.nombre || "Ejercicio"}</strong>
                        <div>Series: {ex?.series || "-"} · Reps: {ex?.repeticiones || "-"} · RPE: {ex?.rpe || "-"} · RIR: {ex?.rir || "-"}</div>
                        {ex?.video && (
                          <a href={ex.video} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb" }}>
                            Ver video
                          </a>
                        )}
                      </li>
                    ))}
                  </ol>
                )}
                {routineDetail.summary?.progresion && (
                  <p style={{ marginTop: 8, fontSize: "0.8rem", color: "#374151" }}>
                    {routineDetail.summary.progresion}
                  </p>
                )}
              </div>
            )}
          </>
        )}
        {dietPlan && (
          <>
            {(hasText || hasRoutineLink || routineDetail) ? <br /> : null}
            <button
              type="button"
              onClick={() => dietKey && toggleCard(dietKey)}
              className="message-action-button message-diet-button"
              style={{ marginTop: hasText || hasRoutineLink || routineDetail ? 6 : 0 }}
            >
              {isDietExpanded ? "Ocultar dieta" : "Ver plan de dieta"}
            </button>
            {isDietExpanded && (
              <div className="diet-card">
                <p style={{ margin: 0, fontWeight: 600 }}>Objetivo: {dietPlan.objective || "equilibrada"}</p>
                <div style={{ fontSize: "0.85rem", marginTop: 6, display: "grid", gap: 4 }}>
                  {dietSummary.calorias && <span><strong>Calorias:</strong> {dietSummary.calorias}</span>}
                  {dietSummary.macros?.proteinas && <span><strong>Proteinas:</strong> {dietSummary.macros.proteinas}</span>}
                  {dietSummary.macros?.carbohidratos && <span><strong>Carbohidratos:</strong> {dietSummary.macros.carbohidratos}</span>}
                  {dietSummary.macros?.grasas && <span><strong>Grasas:</strong> {dietSummary.macros.grasas}</span>}
                </div>
                {dietAdjustments.length > 0 && (
                  <div className="health-warning">
                    <strong>Ajustes de salud:</strong>
                    <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                      {dietAdjustments.map((note, idx) => (
                        <li key={`diet-adjust-${m.id}-${idx}`}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {dietMeals.length > 0 && (
                  <ol style={{ marginTop: 10, paddingLeft: 18, display: "grid", gap: 6 }}>
                    {dietMeals.map((meal, idx) => (
                      <li key={`diet-meal-${m.id}-${idx}`} style={{ fontSize: "0.85rem" }}>
                        <strong>{meal?.name || `Comida ${idx + 1}`}</strong>
                        <div>{Array.isArray(meal?.items) && meal.items.length > 0 ? meal.items.join(", ") : "Sin detalle"}</div>
                        {meal?.notes && <div style={{ marginTop: 4, fontSize: "0.78rem", color: "#374151" }}>Nota: {meal.notes}</div>}
                      </li>
                    ))}
                  </ol>
                )}
                {allergenHits.length > 0 && (
                  <div className="allergen-alert">
                    <strong>Atencion alergias:</strong>
                    <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                      {allergenHits.map((hit, idx) => (
                        <li key={`diet-allergen-${m.id}-${idx}`}>
                          {hit?.meal ? `${hit.meal}: ` : ""}{Array.isArray(hit?.items) ? hit.items.join(", ") : "Revisa ingredientes"}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {dietSummary.hydration && (
                  <p style={{ marginTop: 8, fontSize: "0.8rem", color: "#2563eb" }}>
                    Hidratacion: {dietSummary.hydration}
                  </p>
                )}
                {Array.isArray(dietSummary.allergies) && dietSummary.allergies.length > 0 && (
                  <p style={{ marginTop: 4, fontSize: "0.8rem", color: "#6b7280" }}>
                    Alergias consideradas: {dietSummary.allergies.join(", ")}
                  </p>
                )}
              </div>
            )}
          </>
        )}
        {m.image && (
          <>
            {(hasText || hasRoutineLink || routineDetail || dietPlan) ? <br /> : null}
            <img src={m.image} alt="Imagen enviada por el bot" style={{ display: "block", maxWidth: "100%", borderRadius: 8, marginTop: 6 }} loading="lazy" />
          </>
        )}
        {Array.isArray(m.buttons) && m.buttons.length > 0 && (
          <>
            {(hasText || hasRoutineLink || routineDetail || dietPlan || m.image) ? <br /> : null}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 6 }}>
              {m.buttons.map((b, idx) => {
                const buttonTitle = b?.title || b?.text || b?.label || `Opción ${idx + 1}`;
                const buttonPayload = b?.payload || b?.title || "";
                
                return (
                  <button
                    key={`btn-${m.id}-${idx}`}
                    type="button"
                    onClick={() => {
                      if (buttonPayload) {
                        setInput(buttonPayload);
                        setTimeout(sendMessage, 0);
                      }
                    }}
                    className="quick-reply-button"
                  >
                    {buttonTitle}
                  </button>
                );
              })}
            </div>
          </>
        )}
      </>
    );
  };

  const sendRoutineByEmail = async (routineDetail) => {
    try {
      // Build a simple body for email in case backend needs it
      const lines = [];
      if (routineDetail.header) lines.push(routineDetail.header);
      lines.push("");
      lines.push("Detalle de ejercicios:");
      (routineDetail.exercises || []).forEach((ex) => {
        const name = ex.nombre || ex.name || "Ejercicio";
        const series = ex.series || ex.series || "-";
        const reps = ex.repeticiones || ex.reps || "-";
        lines.push(`- ${name} | ${series} x ${reps}`);
      });

      const payload = {
        body: lines.join("\n"),
        subject: "Tu rutina diaria Fitter",
        attach: true,
        format: "pdf",
        routine_data: routineDetail,
      };

      const res = await fetch("/notifications/daily-routine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert("No se pudo enviar la rutina por correo: " + (err.error || res.status));
        return;
      }

      alert("Rutina enviada por correo correctamente.");
    } catch (e) {
      console.error(e);
      alert("Error al enviar la rutina por correo. Reintenta más tarde.");
    }
  };


  return (
    <div
      className="chatbot-container"
      role="region"
      aria-label="Chat con asistente FITTER"
    >
      <div ref={scrollRef} className="chatbot-messages" aria-live="polite">
        {messages.map((m) => (
          <div key={m.id} className={`chatbot-message ${m.from === "user" ? "user-message" : "bot-message"}`}>
            <Bubble from={m.from}>{renderMessageContent(m)}</Bubble>
          </div>
        ))}
        {loading && <div className="chatbot-loading">Escribiendo…</div>}
      </div>

      {errorText && (
        <div className="chatbot-error" role="alert">
          {errorText}
        </div>
      )}

      <div className="chatbot-input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Escribe tu mensaje…"
          rows={1}
          className="chatbot-textarea"
          aria-label="Cuadro de mensaje"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || input.trim().length === 0}
          className="chatbot-send-button"
          aria-busy={loading}
          aria-label="Enviar mensaje"
        >
          {loading ? "Enviando…" : "Enviar"}
        </button>
      </div>
    </div>
  );
}





