// src/App.js
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Chatbot from "./Chatbot";
import RutinaPage from "/pages/RutinaPages"; // asegúrate que el archivo se llame igual

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Ruta principal: el chatbot */}
        <Route path="/" element={<Chatbot />} />

        {/* Ruta para abrir rutina en nueva pestaña */}
        <Route path="/rutina/:id" element={<RutinaPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
