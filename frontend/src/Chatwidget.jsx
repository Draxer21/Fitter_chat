// ChatWidget.jsx
import { useEffect, useRef, useState } from "react";
import Chatbot from "./Chatbot";

const MIN_WIDTH = 380;
const MIN_HEIGHT = 400;
const FallbackSize = { width: 600, height: 800 };

function clampSize(base) {
  if (typeof window === "undefined") {
    return base;
  }
  const horizontalMargin = 100; // leave space for margins and the launcher button
  const verticalMargin = 110;
  const maxWidth = Math.max(MIN_WIDTH, window.innerWidth - horizontalMargin);
  const maxHeight = Math.max(MIN_HEIGHT, window.innerHeight - verticalMargin);
  return {
    width: Math.min(Math.max(MIN_WIDTH, base.width), maxWidth),
    height: Math.min(Math.max(MIN_HEIGHT, base.height), maxHeight),
  };
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const panelRef = useRef(null);
  const btnRef = useRef(null);
  const panelId = "fw-chat-panel";
  const [panelSize, setPanelSize] = useState(() => {
    try {
      const raw = localStorage.getItem("fw_chat_panel_size");
      if (raw) {
        return clampSize(JSON.parse(raw));
      }
    } catch (e) {}
    return clampSize(FallbackSize);
  });
  const [savedSize, setSavedSize] = useState(null); // Guardar tamaño antes de maximizar
  // resizingRef: { active: boolean, mode: 'h'|'v'|'both' }
  const resizingRef = useRef({ active: false, mode: null });
  const resizeStartRef = useRef({ startX: 0, startY: 0, startWidth: 0, startHeight: 0 });

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

  useEffect(() => {
    const onResize = () => {
      setPanelSize((size) => clampSize(size));
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Resize handlers for the floating panel (horizontal, vertical, corner)
  useEffect(() => {
    const onPointerMove = (e) => {
      if (!resizingRef.current.active) return;
      const { mode } = resizingRef.current;
      const { startX, startY, startWidth, startHeight } = resizeStartRef.current;
      const clientX = e.touches && e.touches[0] ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches && e.touches[0] ? e.touches[0].clientY : e.clientY;

      let newWidth = startWidth;
      let newHeight = startHeight;

      if (mode === "h" || mode === "both") {
        const deltaX = startX - clientX; // moving left increases width
        newWidth = Math.max(MIN_WIDTH, Math.min(window.innerWidth - 50, startWidth + deltaX));
      }
      if (mode === "v" || mode === "both") {
        const deltaY = clientY - startY; // moving down increases height
        newHeight = Math.max(MIN_HEIGHT, Math.min(window.innerHeight - 100, startHeight + deltaY));
      }

      setPanelSize((s) => ({ ...s, width: newWidth, height: newHeight }));
    };

    const onPointerUp = () => {
      if (!resizingRef.current.active) return;
      resizingRef.current = { active: false, mode: null };
      try {
        localStorage.setItem("fw_chat_panel_size", JSON.stringify(panelSize));
      } catch (e) {}
    };

    window.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseup", onPointerUp);
    window.addEventListener("touchmove", onPointerMove, { passive: false });
    window.addEventListener("touchend", onPointerUp);
    return () => {
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("mouseup", onPointerUp);
      window.removeEventListener("touchmove", onPointerMove);
      window.removeEventListener("touchend", onPointerUp);
    };
  }, [panelSize]);

  // Función para maximizar/restaurar el panel
  const toggleMaximize = () => {
    if (isMaximized) {
      // Restaurar tamaño guardado
      if (savedSize) {
        setPanelSize(savedSize);
      }
      setIsMaximized(false);
    } else {
      // Guardar tamaño actual y maximizar
      setSavedSize(panelSize);
      setPanelSize({
        width: window.innerWidth - 50,
        height: window.innerHeight - 100
      });
      setIsMaximized(true);
    }
  };

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
          style={{ width: panelSize.width + "px", height: panelSize.height + "px" }}
        >
          <div className="fw-chat-header">
            <span>Fitter · Asistente</span>
            <button
              className="fw-chat-maximize-btn"
              onClick={toggleMaximize}
              title={isMaximized ? "Restaurar tamaño" : "Maximizar"}
              aria-label={isMaximized ? "Restaurar tamaño" : "Maximizar"}
            >
              {isMaximized ? "⊡" : "⊞"}
            </button>
          </div>
          {/* resize handle placed at left edge to allow horizontal resizing */}
          <div
            className="fw-chat-resizer"
            onMouseDown={(e) => {
              e.preventDefault();
              resizingRef.current = { active: true, mode: "h" };
              resizeStartRef.current = { startX: e.clientX, startY: e.clientY, startWidth: panelSize.width, startHeight: panelSize.height };
            }}
            onTouchStart={(e) => {
              const touch = e.touches && e.touches[0];
              if (!touch) return;
              resizingRef.current = { active: true, mode: "h" };
              resizeStartRef.current = { startX: touch.clientX, startY: touch.clientY, startWidth: panelSize.width, startHeight: panelSize.height };
            }}
            aria-hidden="true"
            title="Arrastra para cambiar ancho"
          />
          {/* bottom resizer for vertical resizing */}
          <div
            className="fw-chat-resizer-vert"
            onMouseDown={(e) => {
              e.preventDefault();
              resizingRef.current = { active: true, mode: "v" };
              resizeStartRef.current = { startX: e.clientX, startY: e.clientY, startWidth: panelSize.width, startHeight: panelSize.height };
            }}
            onTouchStart={(e) => {
              const touch = e.touches && e.touches[0];
              if (!touch) return;
              resizingRef.current = { active: true, mode: "v" };
              resizeStartRef.current = { startX: touch.clientX, startY: touch.clientY, startWidth: panelSize.width, startHeight: panelSize.height };
            }}
            aria-hidden="true"
            title="Arrastra para cambiar altura"
          />
          {/* corner resizer for both width and height */}
          <div
            className="fw-chat-resizer-corner"
            onMouseDown={(e) => {
              e.preventDefault();
              resizingRef.current = { active: true, mode: "both" };
              resizeStartRef.current = { startX: e.clientX, startY: e.clientY, startWidth: panelSize.width, startHeight: panelSize.height };
            }}
            onTouchStart={(e) => {
              const touch = e.touches && e.touches[0];
              if (!touch) return;
              resizingRef.current = { active: true, mode: "both" };
              resizeStartRef.current = { startX: touch.clientX, startY: touch.clientY, startWidth: panelSize.width, startHeight: panelSize.height };
            }}
            aria-hidden="true"
            title="Arrastra para cambiar tamaño"
          />
          <div className="fw-chat-body">
            {/* El Chat usa /chat/send por defecto y UID persistente */}
            <Chatbot />
          </div>
        </div>
      )}
    </>
  );
}
