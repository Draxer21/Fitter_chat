// src/App.js
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Chatbot from "./Chatbot";
import RutinaPage from ".//pages/RutinaPages"; // ajusta la ruta si tu archivo se llama distinto

function App() {
  return (
    <BrowserRouter>
    <header className="app-header">Fitter Chatbot </header>
      <Routes>
        <Route path="/" element={<Chatbot />} />
        <Route path="/rutina/:id" element={<RutinaPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
