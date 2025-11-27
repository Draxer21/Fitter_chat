import { useEffect, useState } from "react";
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

  // Crear nueva conversación
  const createNewConversation = () => {
    const newConv = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      messages: [],
      preview: "Nueva conversación"
    };
    
    const updatedConvs = [newConv, ...conversations].slice(0, MAX_CONVERSATIONS);
    setConversations(updatedConvs);
    setActiveConversationId(newConv.id);
    setActiveMessages([]);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedConvs));
  };

  // Seleccionar conversación existente
  const selectConversation = (convId) => {
    const conv = conversations.find(c => c.id === convId);
    if (conv) {
      setActiveConversationId(convId);
      setActiveMessages(conv.messages || []);
    }
  };

  // Eliminar conversación
  const deleteConversation = (convId, event) => {
    event.stopPropagation(); // Evitar que se seleccione la conversación al hacer click en eliminar
    
    const updatedConvs = conversations.filter(c => c.id !== convId);
    setConversations(updatedConvs);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedConvs));
    
    // Si se eliminó la conversación activa, seleccionar otra o limpiar
    if (convId === activeConversationId) {
      if (updatedConvs.length > 0) {
        setActiveConversationId(updatedConvs[0].id);
        setActiveMessages(updatedConvs[0].messages || []);
      } else {
        setActiveConversationId(null);
        setActiveMessages([]);
      }
    }
  };

  // Actualizar conversación activa con nuevo mensaje
  const updateActiveConversation = (newMessage) => {
    const updatedConvs = conversations.map(conv => {
      if (conv.id === activeConversationId) {
        const updatedMessages = [...(conv.messages || []), newMessage];
        return {
          ...conv,
          messages: updatedMessages,
          preview: newMessage.text?.substring(0, 50) || "Conversación",
          timestamp: new Date().toISOString()
        };
      }
      return conv;
    });

    // Ordenar por timestamp más reciente
    updatedConvs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    setConversations(updatedConvs);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedConvs));
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
            <div className="chat-header">
              <div className="d-flex align-items-center">
                <img
                  src="/fitter_logo.png"
                  alt="Fitter Assistant"
                  className="chat-avatar me-3"
                />
                <div>
                  <h1 className="h4 mb-0">Asistente Virtual Fitter</h1>
                  <p className="text-muted small mb-0">
                    <i className="fa-solid fa-circle text-success me-2" aria-hidden="true" />
                    En línea · Siempre disponible
                  </p>
                </div>
              </div>
            </div>

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
                  // Si no hay conversación activa, crear una
                  if (!activeConversationId) {
                    createNewConversation();
                  }
                  
                  // Actualizar la conversación activa
                  updateActiveConversation({
                    text: msg,
                    timestamp: new Date().toISOString(),
                    from: "user"
                  });
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
