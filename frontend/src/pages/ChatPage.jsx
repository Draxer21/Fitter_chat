import { useEffect, useState } from "react";
import Chatbot from "../Chatbot";
import { useAuth } from "../contexts/AuthContext";
import "../styles/ChatPage.css";

export default function ChatPage() {
  const { isAuthenticated } = useAuth();
  const [chatHistory, setChatHistory] = useState([]);

  // Cargar historial de chats del localStorage
  useEffect(() => {
    const loadHistory = () => {
      const saved = localStorage.getItem("fitter_chat_history");
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setChatHistory(parsed);
        } catch (e) {
          console.error("Error loading chat history:", e);
        }
      }
    };
    loadHistory();
  }, []);

  return (
    <main className="chat-page">
      <div className="container-fluid h-100">
        <div className="row h-100">
          {/* Sidebar con historial */}
          <div className="col-md-3 chat-sidebar">
            <div className="sidebar-header">
              <h2 className="h5 mb-0">
                <i className="fa-solid fa-message me-2" aria-hidden="true" />
                Historial de Chats
              </h2>
            </div>
            <div className="sidebar-content">
              {chatHistory.length === 0 ? (
                <div className="text-muted text-center py-4">
                  <i className="fa-solid fa-comments fa-3x mb-3 opacity-25" aria-hidden="true" />
                  <p>No hay conversaciones previas</p>
                  <small>Inicia una conversación para ver el historial</small>
                </div>
              ) : (
                <div className="chat-history-list">
                  {chatHistory.map((chat, idx) => (
                    <div key={idx} className="chat-history-item">
                      <div className="chat-date">
                        <i className="fa-solid fa-clock me-2" aria-hidden="true" />
                        {new Date(chat.timestamp).toLocaleDateString("es-CL", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                      <div className="chat-preview">{chat.preview || "Conversación"}</div>
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
                onNewMessage={(msg) => {
                  // Guardar en historial cuando hay un mensaje nuevo
                  const newHistory = [
                    {
                      timestamp: new Date().toISOString(),
                      preview: msg.substring(0, 50),
                    },
                    ...chatHistory.slice(0, 19), // Máximo 20 chats
                  ];
                  setChatHistory(newHistory);
                  localStorage.setItem("fitter_chat_history", JSON.stringify(newHistory));
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
