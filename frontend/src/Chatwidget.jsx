// ChatWidget.jsx
import { useEffect, useRef, useState } from "react";
import Chatbot from "./Chatbot";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const panelRef = useRef(null);
  const btnRef = useRef(null);
  const panelId = "fw-chat-panel";

  // Cerrar con tecla Escape y devolver foco al botón
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") {
        setOpen(false);
        btnRef.current?.focus();
      }
    };
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      {/* Botón flotante (burbuja) */}
      <button
        ref={btnRef}
        className="fw-chat-launcher"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Cerrar chat" : "Abrir chat"}
        aria-expanded={open}
        aria-controls={panelId}
        type="button"
      >
        {open ? "×" : "💬"}
      </button>

      {/* Panel del chat */}
      {open && (
        <div
          id={panelId}
          ref={panelRef}
          className="fw-chat-panel"
          role="dialog"
          aria-modal="false"
          aria-label="Chat Fitter"
        >
          <div className="fw-chat-header">Fitter · Asistente</div>
          <div className="fw-chat-body">
            {/* El Chat usa /chat/send por defecto y UID persistente */}
            <Chatbot />
          </div>
        </div>
      )}
    </>
  );
}
