import { useEffect, useRef, useState } from "react";
import Chatbot from "../Chatbot";
import "../styles/ChatPage.css";

const STORAGE_KEY = "fitter_chat_conversations";
const MAX_CONVERSATIONS = 50;

export default function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [activeMessages, setActiveMessages] = useState([]);

  // Ref siempre actualizado: evita stale closure dentro de callbacks async
  const activeConvIdRef = useRef(null);

  // Cargar conversaciones del localStorage
  useEffect(() => {
    const loadConversations = () => {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setConversations(parsed);
          
          // Si hay conversaciones, seleccionar la más reciente
          if (parsed.length > 0) {
            const latest = parsed[0];
            setActiveConversationId(latest.id);
            setActiveMessages(latest.messages || []);
          }
        } catch (e) {
          console.error("Error loading conversations:", e);
        }
      }
    };
    loadConversations();
  }, []);

  // Mantener ref sincronizado con el estado
  useEffect(() => {
    activeConvIdRef.current = activeConversationId;
  }, [activeConversationId]);

  // Crear nueva conversación — devuelve el id creado para uso inmediato
  const createNewConversation = () => {
    const newConv = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      messages: [],
      preview: "Nueva conversación"
    };

    activeConvIdRef.current = newConv.id;
    setActiveConversationId(newConv.id);
    setActiveMessages([]);
    setConversations(prev => {
      const updated = [newConv, ...prev].slice(0, MAX_CONVERSATIONS);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });

    return newConv.id;
  };

  // Seleccionar conversación existente
  const selectConversation = (convId) => {
    const conv = conversations.find(c => c.id === convId);
    if (conv) {
      activeConvIdRef.current = convId;
      setActiveConversationId(convId);
      setActiveMessages(conv.messages || []);
    }
  };

  // Eliminar conversación
  const deleteConversation = (convId, event) => {
    event.stopPropagation();

    const wasActive = convId === activeConvIdRef.current;

    setConversations(prev => {
      const updated = prev.filter(c => c.id !== convId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

      if (wasActive) {
        if (updated.length > 0) {
          activeConvIdRef.current = updated[0].id;
          setActiveConversationId(updated[0].id);
          setActiveMessages(updated[0].messages || []);
        } else {
          activeConvIdRef.current = null;
          setActiveConversationId(null);
          setActiveMessages([]);
        }
      }

      return updated;
    });
  };

  // Agregar un mensaje a la conversación activa.
  // Usa setConversations(prev => ...) para evitar stale closure cuando
  // onNewMessage y onBotMessage se disparan en secuencia async.
  const appendMessageToConversation = (convId, newMessage) => {
    setConversations(prev => {
      const updated = prev.map(conv => {
        if (conv.id !== convId) return conv;
        const messages = [...(conv.messages || []), newMessage];
        const previewText = newMessage.from === "user"
          ? newMessage.text?.substring(0, 50)
          : conv.preview; // mantener preview del último mensaje de usuario
        return {
          ...conv,
          messages,
          preview: previewText || conv.preview || "Conversación",
          timestamp: new Date().toISOString()
        };
      });
      updated.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <main className="chat-page">
      {/* ── Sidebar ── */}
      <aside className="chat-sidebar">
        <div className="sidebar-header">
          <span className="sidebar-title">
            <i className="fa-solid fa-message me-1" aria-hidden="true" />
            Chats
          </span>
          <button
            className="btn btn-sm btn-success new-chat-btn"
            onClick={createNewConversation}
            title="Nueva conversación"
            aria-label="Crear nueva conversación"
          >
            <i className="fa-solid fa-plus" aria-hidden="true" />
          </button>
        </div>

        <div className="sidebar-content">
          {conversations.length === 0 ? (
            <div className="text-muted text-center py-4">
              <i className="fa-solid fa-comments fa-3x mb-3 opacity-25" aria-hidden="true" />
              <p className="mb-1" style={{ fontSize: "0.85rem" }}>Sin conversaciones</p>
              <small>Pulsa + para empezar</small>
            </div>
          ) : (
            <div className="chat-history-list">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`chat-history-item ${conv.id === activeConversationId ? "active" : ""}`}
                  onClick={() => selectConversation(conv.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === "Enter" && selectConversation(conv.id)}
                >
                  <div className="chat-item-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2px" }}>
                    <div className="chat-date">
                      {new Date(conv.timestamp).toLocaleDateString("es-CL", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                    <button
                      className="btn-delete-chat"
                      onClick={(e) => deleteConversation(conv.id, e)}
                      title="Eliminar conversación"
                      aria-label="Eliminar conversación"
                      style={{
                        background: "transparent",
                        border: "1px solid #ef4444",
                        color: "#ef4444",
                        padding: "1px 5px",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontSize: "11px",
                        flexShrink: 0,
                        lineHeight: 1,
                        fontWeight: 700,
                      }}
                    >
                      ✕
                    </button>
                  </div>
                  <div className="chat-preview">{conv.preview || "Conversación"}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* ── Área de chat — sin wrapper extra ── */}
      <section className="chat-main">
        <Chatbot
          pageMode={true}
          initialMessages={activeMessages}
          onNewMessage={(msg) => {
            let convId = activeConvIdRef.current;
            if (!convId) convId = createNewConversation();
            appendMessageToConversation(convId, {
              text: msg,
              from: "user",
              timestamp: new Date().toISOString(),
            });
          }}
          onBotMessage={(botMsg) => {
            const convId = activeConvIdRef.current;
            if (convId) appendMessageToConversation(convId, botMsg);
          }}
        />
      </section>
    </main>
  );
}
