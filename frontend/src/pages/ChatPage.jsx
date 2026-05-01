import { useEffect, useRef, useState } from "react";
import Chatbot from "../Chatbot";
import { useAuth } from "../contexts/AuthContext";
import "../styles/ChatPage.css";

const STORAGE_KEY = "fitter_chat_conversations";
const MAX_CONVERSATIONS = 50;

export default function ChatPage() {
  const { isAuthenticated } = useAuth();
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
      <div className="container-fluid h-100">
        <div className="row h-100">
          {/* Sidebar con historial */}
          <div className="col-md-3 chat-sidebar">
            <div className="sidebar-header">
              <div className="d-flex justify-content-between align-items-center">
                <h2 className="h5 mb-0">
                  <i className="fa-solid fa-message me-2" aria-hidden="true" />
                  Conversaciones
                </h2>
                <button 
                  className="btn btn-sm btn-success new-chat-btn"
                  onClick={createNewConversation}
                  title="Nueva conversación"
                  aria-label="Crear nueva conversación"
                >
                  +
                </button>
              </div>
            </div>
            <div className="sidebar-content">
              {conversations.length === 0 ? (
                <div className="text-muted text-center py-4">
                  <i className="fa-solid fa-comments fa-3x mb-3 opacity-25" aria-hidden="true" />
                  <p>No hay conversaciones</p>
                  <small>Haz clic en + para crear una</small>
                </div>
              ) : (
                <div className="chat-history-list">
                  {conversations.map((conv) => (
                    <div 
                      key={conv.id} 
                      className={`chat-history-item ${conv.id === activeConversationId ? 'active' : ''}`}
                      onClick={() => selectConversation(conv.id)}
                    >
                      <div className="chat-item-header">
                        <div className="chat-date">
                          <i className="fa-solid fa-clock me-2" aria-hidden="true" />
                          {new Date(conv.timestamp).toLocaleDateString("es-CL", {
                            day: "2-digit",
                            month: "short",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                        <button
                          className="btn-delete-chat"
                          onClick={(e) => deleteConversation(conv.id, e)}
                          title="Eliminar conversación"
                          aria-label="Eliminar conversación"
                        >
                          <i className="fa-solid fa-trash" aria-hidden="true" />
                        </button>
                      </div>
                      <div className="chat-preview">{conv.preview || "Conversación"}</div>
                      <div className="chat-message-count">
                        <i className="fa-solid fa-message me-1" aria-hidden="true" />
                        {conv.messages?.length || 0} mensajes
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Panel principal del chat */}
          <div className="col-md-9 chat-main">
            <div className="chat-container">
              <div className="welcome-banner mb-4">
                <h3>
                  <i className="fa-solid fa-robot me-2" aria-hidden="true" />
                  ¡Hola{isAuthenticated ? "" : " visitante"}!
                </h3>
                <p className="mb-2">
                  Soy tu asistente virtual de Fitter. Puedo ayudarte con:
                </p>
                <div className="capabilities-grid">
                  <div className="capability-item">
                    <i className="fa-solid fa-dumbbell" aria-hidden="true" />
                    <span>Rutinas personalizadas</span>
                  </div>
                  <div className="capability-item">
                    <i className="fa-solid fa-utensils" aria-hidden="true" />
                    <span>Planes nutricionales</span>
                  </div>
                  <div className="capability-item">
                    <i className="fa-solid fa-user-circle" aria-hidden="true" />
                    <span>Gestión de perfil</span>
                  </div>
                  <div className="capability-item">
                    <i className="fa-solid fa-calendar-check" aria-hidden="true" />
                    <span>Consulta de reservas</span>
                  </div>
                  <div className="capability-item">
                    <i className="fa-solid fa-question-circle" aria-hidden="true" />
                    <span>Soporte general</span>
                  </div>
                  <div className="capability-item">
                    <i className="fa-solid fa-shield-halved" aria-hidden="true" />
                    <span>Ayuda con MFA</span>
                  </div>
                </div>
              </div>

              <Chatbot
                initialMessages={activeMessages}
                onNewMessage={(msg) => {
                  // Asegurar conversación activa (sync via ref)
                  let convId = activeConvIdRef.current;
                  if (!convId) {
                    convId = createNewConversation();
                  }
                  appendMessageToConversation(convId, {
                    text: msg,
                    from: "user",
                    timestamp: new Date().toISOString()
                  });
                }}
                onBotMessage={(botMsg) => {
                  const convId = activeConvIdRef.current;
                  if (convId) {
                    appendMessageToConversation(convId, botMsg);
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
