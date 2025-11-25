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

export default function Chatbot({ endpoint = "/chat/send", senderId, onNewMessage }) {
  const uidRef = useRef(senderId || getOrCreateSenderId());

  const [messages, setMessages] = useState(() => [
    { id: 1, from: "bot", text: "¡Hola! Soy FITTER. ¿En qué te ayudo?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState("");
  const [expandedCards, setExpandedCards] = useState({});
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

    // Llamar callback si existe
    if (onNewMessage && typeof onNewMessage === "function") {
      onNewMessage(text);
    }

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

  const toggleCard = (key) => {
    setExpandedCards((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const Bubble = ({ children, from }) => (
    <div
      className="message"
      style={{
        display: "inline-block",
        padding: "8px 12px",
        borderRadius: from === "user" ? "16px 16px 0 16px" : "16px 16px 16px 0",
        background: from === "user" ? "#DCF8C6" : "#F1F0F0",
        color: from === "user" ? "#0b1120" : "#111827",
        maxWidth: "85%",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word"
      }}
    >
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
              style={{ marginTop: hasText ? 6 : 0, padding: "6px 12px", borderRadius: 8, border: "none", background: "#007bff", color: "white", cursor: "pointer" }}
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
              style={{ marginTop: hasText || hasRoutineLink ? 6 : 0, padding: "6px 12px", borderRadius: 8, border: "1px solid #2563eb", background: "#1d4ed8", color: "white", cursor: "pointer" }}
            >
              {isRoutineExpanded ? "Ocultar rutina" : "Ver rutina aqui"}
            </button>
            {isRoutineExpanded && (
              <div style={{ marginTop: 8, background: "rgba(255,255,255,0.85)", padding: "8px 10px", borderRadius: 8, textAlign: "left", lineHeight: 1.45 }}>
                {routineDetail.header && <p style={{ margin: 0, fontWeight: 600 }}>{routineDetail.header}</p>}
                <div style={{ fontSize: "0.85rem", marginTop: 6, display: "grid", gap: 4 }}>
                  <span><strong>Tiempo:</strong> {routineDetail.summary?.tiempo_min ?? "-"} min</span>
                  <span><strong>Ejercicios:</strong> {routineDetail.summary?.ejercicios ?? "-"}</span>
                  <span><strong>Equipo:</strong> {routineDetail.summary?.equipamiento ?? "-"}</span>
                  <span><strong>Objetivo:</strong> {routineDetail.summary?.objetivo ?? "-"}</span>
                  <span><strong>Nivel:</strong> {routineDetail.summary?.nivel ?? "-"}</span>
                </div>
                {Array.isArray(routineDetail.summary?.health_notes) && routineDetail.summary.health_notes.length > 0 && (
                  <div style={{ marginTop: 8, fontSize: "0.8rem", background: "#FEF3C7", borderRadius: 8, padding: "6px 8px", color: "#92400e" }}>
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
              style={{ marginTop: hasText || hasRoutineLink || routineDetail ? 6 : 0, padding: "6px 12px", borderRadius: 8, border: "1px solid #059669", background: "#047857", color: "white", cursor: "pointer" }}
            >
              {isDietExpanded ? "Ocultar dieta" : "Ver plan de dieta"}
            </button>
            {isDietExpanded && (
              <div style={{ marginTop: 8, background: "rgba(236, 253, 245, 0.9)", padding: "8px 10px", borderRadius: 8, textAlign: "left", lineHeight: 1.45 }}>
                <p style={{ margin: 0, fontWeight: 600 }}>Objetivo: {dietPlan.objective || "equilibrada"}</p>
                <div style={{ fontSize: "0.85rem", marginTop: 6, display: "grid", gap: 4 }}>
                  {dietSummary.calorias && <span><strong>Calorias:</strong> {dietSummary.calorias}</span>}
                  {dietSummary.macros?.proteinas && <span><strong>Proteinas:</strong> {dietSummary.macros.proteinas}</span>}
                  {dietSummary.macros?.carbohidratos && <span><strong>Carbohidratos:</strong> {dietSummary.macros.carbohidratos}</span>}
                  {dietSummary.macros?.grasas && <span><strong>Grasas:</strong> {dietSummary.macros.grasas}</span>}
                </div>
                {dietAdjustments.length > 0 && (
                  <div style={{ marginTop: 8, fontSize: "0.8rem", background: "#fef3c7", borderRadius: 8, padding: "6px 8px", color: "#b45309" }}>
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
                  <div style={{ marginTop: 8, fontSize: "0.8rem", background: "#fee2e2", borderRadius: 8, padding: "6px 8px", color: "#b91c1c" }}>
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
                    style={{ 
                      padding: "8px 16px", 
                      borderRadius: 8, 
                      border: "1px solid #d1d5db", 
                      background: "#ffffff", 
                      color: "#1f2937",
                      cursor: "pointer",
                      fontSize: "0.9rem",
                      fontWeight: "500",
                      transition: "all 0.2s"
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#f3f4f6";
                      e.currentTarget.style.borderColor = "#9ca3af";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "#ffffff";
                      e.currentTarget.style.borderColor = "#d1d5db";
                    }}
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





