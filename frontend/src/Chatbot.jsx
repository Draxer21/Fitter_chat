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

export default function Chatbot({ endpoint = "/chat/send", senderId, onNewMessage, onBotMessage, initialMessages = [] }) {
  const uidRef = useRef(senderId || getOrCreateSenderId());

  const CONSENT_KEY = "fitter_chat_consent";
  const [consent, setConsent] = useState(() => localStorage.getItem(CONSENT_KEY) === "1");

  const onConsentChange = (checked) => {
    setConsent(checked);
    try {
      localStorage.setItem(CONSENT_KEY, checked ? "1" : "0");
    } catch (e) {
      // ignore
    }
    if (checked) setErrorText("");
  };

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
    
    // Notificar los mensajes del bot al componente padre
    if (onBotMessage && typeof onBotMessage === "function") {
      botMsgs.forEach(msg => {
        if (msg.text) {
          onBotMessage({ text: msg.text, from: "bot", timestamp: new Date().toISOString() });
        }
      });
    }
  };

  const sendText = async (outgoingText, displayText) => {
    const text = (outgoingText || "").trim();
    if (!consent) {
      setErrorText("Debes aceptar las condiciones de uso del chatbot para enviar mensajes.");
      return false;
    }
    if (!text || loading) return false;

    setErrorText("");
    if (displayText !== false) {
      pushMessage({ from: "user", text: typeof displayText === "string" ? displayText : text });
    }
    setLoading(true);

    if (onNewMessage && typeof onNewMessage === "function") {
      onNewMessage(text);
    }

    try {
      await sendToBackend(text);
      return true;
    } catch (e) {
      const msg = e?.name === "AbortError" ? "Solicitud cancelada." : "Error de conexión con el backend.";
      setErrorText(typeof e?.message === "string" ? e.message : msg);
      pushMessage({ from: "bot", text: "Error de conexión con el backend." });
      return false;
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    const text = input.trim();
    const sent = await sendText(text, text);
    if (sent) {
      setInput("");
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

  const openDietView = (diet) => {
    try {
      if (!diet) {
        console.error("No diet data provided");
        alert("No hay datos de dieta disponibles");
        return;
      }
      
      // Log para debugging
      console.log("Diet data:", diet);
      console.log("Diet meals:", diet.meals);
      if (diet.meals && diet.meals.length > 0) {
        console.log("First meal items:", diet.meals[0].items);
        console.log("First item type:", typeof diet.meals[0].items[0]);
      }
      
      // If server provided a direct URL (PDF or hosted page), open it
      if (diet.url && typeof diet.url === "string") {
        window.open(diet.url, "_blank", "noopener,noreferrer");
        return;
      }

      // Validate that we have some content to display
      const hasMeals = Array.isArray(diet.meals) && diet.meals.length > 0;
      const hasSummary = diet.summary && typeof diet.summary === 'object';
      
      if (!hasMeals && !hasSummary) {
        console.error("Diet has no meals or summary");
        alert("El plan de dieta no tiene información suficiente para mostrar");
        return;
      }

      // Otherwise create a printable HTML page with the diet content
      const escapeHtml = (s) => String(s === null || s === undefined ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");

      const mealsHtml = (Array.isArray(diet.meals) ? diet.meals : []).map((meal, idx) => {
        // Handle both string arrays (old format) and object arrays (catalog format)
        const items = meal?.items;
        let itemsText = "Sin detalle";
        if (Array.isArray(items) && items.length > 0) {
          if (typeof items[0] === 'string') {
            // Old format: array of strings
            itemsText = items.join(", ");
          } else if (typeof items[0] === 'object' && items[0]?.name) {
            // Catalog format: array of {name, qty, kcal}
            itemsText = items.map(it => 
              `${it.name} (${it.qty || '100g'}${it.kcal ? `, ${it.kcal} kcal` : ''})`
            ).join(", ");
          }
        }
        return `
        <li style="margin-bottom:10px">
          <strong>${escapeHtml(meal?.name || `Comida ${idx + 1}`)}</strong>
          <div style="margin-top:6px">${escapeHtml(itemsText)}</div>
          ${meal?.notes ? `<div style="margin-top:6px;font-size:0.9rem;color:#374151">Nota: ${escapeHtml(meal.notes)}</div>` : ""}
        </li>`;
      }).join("");

      const adjustmentsHtml = (Array.isArray(diet.summary?.health_adjustments) ? diet.summary.health_adjustments : [])
        .map(a => `<li>${escapeHtml(a)}</li>`).join("");

      const allergensHtml = (Array.isArray(diet.summary?.allergies) ? diet.summary.allergies : [])
        .map(a => `<span style="margin-right:6px">${escapeHtml(a)}</span>`).join("");

      console.log("=== GENERATING HTML ===");
      console.log("Meals HTML length:", mealsHtml.length);
      console.log("Adjustments HTML length:", adjustmentsHtml.length);

      const html = `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Plan de dieta - FITTER</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #111827; padding: 20px; margin: 0; background: #ffffff; }
    .container { max-width: 900px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #4CAF50; }
    h1 { font-size: 1.8rem; margin: 0; color: #4CAF50; }
    .meta { color: #6b7280; font-size: 0.95rem; }
    .card { background: #f8fafc; padding: 20px; border-radius: 12px; margin-top: 16px; border: 1px solid #e5e7eb; }
    .info-row { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px; }
    .info-item { flex: 1; min-width: 150px; }
    .info-item strong { color: #374151; }
    .meals { margin-top: 20px; }
    .meals h3 { margin: 0 0 12px 0; color: #374151; font-size: 1.2rem; }
    .meals ol { padding-left: 20px; }
    .meals li { margin-bottom: 12px; }
    .meals li strong { color: #059669; }
    .actions { margin-top: 20px; display: flex; gap: 10px; }
    button { padding: 10px 20px; border-radius: 8px; border: none; background: #4CAF50; color: #fff; cursor: pointer; font-size: 1rem; font-weight: 500; transition: background 0.2s; }
    button:hover { background: #45a049; }
    button.secondary { background: #6b7280; }
    button.secondary:hover { background: #4b5563; }
    .print-only { display: block; }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.9rem; text-align: center; }
    ul { margin: 8px 0; padding-left: 20px; }
    ul li { margin-bottom: 5px; }
    @media print { .print-only { display: none !important; } button { display: none !important; } }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Plan de Dieta</h1>
      <div class="meta">Objetivo: ${escapeHtml(diet.objective || diet.summary?.objective || "equilibrada")}</div>
    </header>

    <div class="card">
      <div class="info-row">
        ${diet.summary?.calorias ? `<div class="info-item"><strong>Calorías:</strong> ${escapeHtml(diet.summary.calorias)}</div>` : ""}
        ${diet.summary?.macros?.proteinas ? `<div class="info-item"><strong>Proteínas:</strong> ${escapeHtml(diet.summary.macros.proteinas)}</div>` : ""}
        ${diet.summary?.macros?.carbohidratos ? `<div class="info-item"><strong>Carbohidratos:</strong> ${escapeHtml(diet.summary.macros.carbohidratos)}</div>` : ""}
        ${diet.summary?.macros?.grasas ? `<div class="info-item"><strong>Grasas:</strong> ${escapeHtml(diet.summary.macros.grasas)}</div>` : ""}
      </div>

      ${adjustmentsHtml ? `<div style="margin-top:15px"><strong style="color:#374151">Ajustes de salud:</strong><ul>${adjustmentsHtml}</ul></div>` : ""}
      ${allergensHtml ? `<div style="margin-top:15px"><strong style="color:#374151">Alergias consideradas:</strong><div style="margin-top:5px">${allergensHtml}</div></div>` : ""}

      <div class="meals">
        <h3>Menú Diario</h3>
        <ol>${mealsHtml || '<li>No hay comidas disponibles</li>'}</ol>
      </div>

      ${diet.summary?.hydration ? `<p style="margin-top:15px;color:#0ea5a4;font-weight:500"><strong>💧 Hidratación:</strong> ${escapeHtml(diet.summary.hydration)}</p>` : ""}
    </div>

    <div class="actions print-only">
      <button onclick="window.print()">🖨️ Imprimir / Guardar PDF</button>
      <button class="secondary" onclick="window.close()">Cerrar</button>
    </div>
    
    <div class="footer">
      <p>Generado por <strong>FITTER</strong> — Consulta con un profesional de la salud antes de realizar cambios significativos en tu dieta.</p>
    </div>
  </div>
</body>
</html>`;

      console.log("HTML generated, length:", html.length);
      
      const w = window.open("", "_blank", "noopener,noreferrer");
      if (!w) {
        console.error("Failed to open window - popup blocked?");
        alert("No se pudo abrir la ventana. Por favor, permite ventanas emergentes para este sitio.");
        return;
      }

      console.log("Window opened successfully");

      try {
        w.document.open();
        w.document.write(html);
        w.document.close();
        console.log("HTML written successfully");
      } catch (err) {
        console.error("Error writing document:", err);
        alert("No se pudo generar el documento. Intenta de nuevo.");
        try {
          w.close();
        } catch (e) {
          console.error("Could not close window:", e);
        }
        return;
      }
      
      // Esperar a que el documento cargue antes de dar foco
      setTimeout(() => {
        try {
          w.focus();
        } catch (e) {
          console.log("Could not focus window");
        }
      }, 100);
    } catch (e) {
      console.error("openDietView error", e);
      alert("Error al abrir el plan de dieta: " + e.message);
    }
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
              onClick={() => sendDietByEmail(dietPlan)}
              className="message-action-button message-diet-button"
              style={{ marginTop: hasText || hasRoutineLink || routineDetail ? 6 : 0 }}
              title="Enviar plan de dieta a tu correo electrónico"
            >
              📧 Enviar al Correo
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
                    {dietMeals.map((meal, idx) => {
                      // Handle both string arrays (old format) and object arrays (catalog format)
                      const items = meal?.items;
                      let itemsDisplay = "Sin detalle";
                      if (Array.isArray(items) && items.length > 0) {
                        if (typeof items[0] === 'string') {
                          // Old format: array of strings
                          itemsDisplay = items.join(", ");
                        } else if (typeof items[0] === 'object' && items[0]?.name) {
                          // Catalog format: array of {name, qty, kcal}
                          itemsDisplay = items.map(it => 
                            `${it.name} (${it.qty || '100g'}${it.kcal ? `, ${it.kcal} kcal` : ''})`
                          ).join(", ");
                        }
                      }
                      return (
                        <li key={`diet-meal-${m.id}-${idx}`} style={{ fontSize: "0.85rem" }}>
                          <strong>{meal?.name || `Comida ${idx + 1}`}</strong>
                          <div>{itemsDisplay}</div>
                          {meal?.notes && <div style={{ marginTop: 4, fontSize: "0.78rem", color: "#374151" }}>Nota: {meal.notes}</div>}
                        </li>
                      );
                    })}
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
                        sendText(buttonPayload, buttonTitle);
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

  const sendDietByEmail = async (dietPlan) => {
    try {
      if (!dietPlan) {
        alert("No hay datos de dieta para enviar");
        return;
      }

      console.log("=== SEND DIET BY EMAIL ===");
      console.log("Diet plan:", dietPlan);
      console.log("Meals:", dietPlan.meals);

      // Construir el cuerpo del correo
      const lines = [];
      lines.push("Plan de Dieta - Fitter");
      lines.push("");
      lines.push(`Objetivo: ${dietPlan.objective || 'equilibrada'}`);
      lines.push("");
      
      if (dietPlan.summary) {
        if (dietPlan.summary.calorias) {
          lines.push(`Calorías: ${dietPlan.summary.calorias}`);
        }
        if (dietPlan.summary.macros) {
          lines.push("Macros:");
          if (dietPlan.summary.macros.proteinas) lines.push(`- Proteínas: ${dietPlan.summary.macros.proteinas}`);
          if (dietPlan.summary.macros.carbohidratos) lines.push(`- Carbohidratos: ${dietPlan.summary.macros.carbohidratos}`);
          if (dietPlan.summary.macros.grasas) lines.push(`- Grasas: ${dietPlan.summary.macros.grasas}`);
        }
      }
      
      lines.push("");
      lines.push("Comidas del día:");
      (dietPlan.meals || []).forEach((meal, idx) => {
        lines.push(`${idx + 1}. ${meal.name || 'Comida'}`);
        if (Array.isArray(meal.items)) {
          meal.items.forEach(item => {
            // Handle both string format and object format {name, qty, kcal}
            if (typeof item === 'string') {
              lines.push(`   - ${item}`);
            } else if (typeof item === 'object' && item.name) {
              const itemText = `${item.name} (${item.qty || '100g'}${item.kcal ? `, ${item.kcal} kcal` : ''})`;
              lines.push(`   - ${itemText}`);
            }
          });
        }
      });

      const payload = {
        body: lines.join("\n"),
        subject: "Tu plan de dieta - Fitter",
        attach: true,
        format: "pdf",
        diet_data: dietPlan,
      };

      const res = await fetch("/notifications/diet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      console.log("Response status:", res.status);
      console.log("Response ok:", res.ok);

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("Error response:", err);
        alert("No se pudo enviar la dieta por correo: " + (err.error || res.status));
        return;
      }

      const result = await res.json();
      console.log("Success response:", result);
      alert("Dieta enviada por correo correctamente.");
    } catch (e) {
      console.error(e);
      alert("Error al enviar la dieta por correo. Reintenta más tarde.");
    }
  };


  return (
    <div
      className="chatbot-container"
      role="region"
      aria-label="Chat con asistente FITTER"
    >
      {/* Consent overlay: si no acepta, bloquea la interacción */}
      {!consent && (
        <div className="chatbot-consent-overlay" role="dialog" aria-label="Consentimiento chatbot">
          <div className="chatbot-consent-panel">
            <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => onConsentChange(e.target.checked)}
                aria-label="Aceptar condiciones de uso del chatbot"
              />
              <span style={{ fontSize: "0.95rem" }}>Acepto las condiciones de uso del chatbot y autorizo el procesamiento de los datos necesarios para su funcionamiento.</span>
            </label>
            <div style={{ marginTop: 12 }}>
              <button
                type="button"
                onClick={() => onConsentChange(true)}
                className="chatbot-send-button"
                aria-label="Aceptar y continuar"
              >
                Aceptar y continuar
              </button>
            </div>
          </div>
        </div>
      )}
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
          disabled={loading || !consent}
        />
        <button
          onClick={sendMessage}
          disabled={loading || input.trim().length === 0 || !consent}
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





