// src/pages/RutinaPage.jsx
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";

export default function RutinaPage() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [rutina, setRutina] = useState(null);
  const [error, setError] = useState(null);

  // INTENTO 1 (opcional): pedir al backend si existiera un endpoint REST
  // Si no lo tienes aún, esto fallará y pasará al INTENTO 2 (fallback local).
  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        // Ajusta este endpoint cuando lo implementes en Flask/Rasa.
        const res = await fetch(`/chat/routine/${id}`);
        if (cancel) return;
        if (res.ok) {
          const data = await res.json();
          setRutina(data);
        } else {
          // Fallback local si el endpoint no existe
          setRutina(fallbackDesdeId(id));
        }
      } catch (e) {
        setRutina(fallbackDesdeId(id));
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [id]);

  if (loading) return <main className="p-6">Cargando rutina…</main>;
  if (error)   return <main className="p-6 text-red-600">Error: {String(error)}</main>;
  if (!rutina) return <main className="p-6">No se encontró la rutina.</main>;

  const { objetivo, musculo, nivel, ejercicios = [], notas } = rutina;

  return (
    <main className="p-6" style={{ maxWidth: 840, margin: "0 auto" }}>
      <header style={{ marginBottom: 16 }}>
        <h1 className="text-2xl font-semibold">Rutina: {titulo(musculo)} · {nivel}</h1>
        <p style={{ color: "#555" }}>Objetivo: <strong>{objetivo}</strong></p>
        <p style={{ color: "#777" }}>ID: {id}</p>
      </header>

      <section style={{ background: "#fafafa", padding: 16, borderRadius: 12, border: "1px solid #eee" }}>
        <h2 className="text-xl" style={{ marginBottom: 8 }}>Bloques de ejercicio</h2>
        <ol style={{ paddingLeft: 18, lineHeight: 1.7 }}>
          {ejercicios.map((e, idx) => <li key={idx}>{e}</li>)}
        </ol>

        {notas && (
          <>
            <h3 style={{ marginTop: 16, marginBottom: 6 }}>Notas</h3>
            <p>{notas}</p>
          </>
        )}
      </section>

      <footer style={{ marginTop: 20, display: "flex", gap: 8 }}>
        <Link to="/" style={{ padding: "8px 12px", border: "1px solid #ccc", borderRadius: 8 }}>
          Volver al chat
        </Link>
        <button
          onClick={() => window.print()}
          style={{ padding: "8px 12px", borderRadius: 8, background: "#0d6efd", color: "white", border: "none" }}
        >
          Imprimir / Guardar PDF
        </button>
      </footer>
    </main>
  );
}

/** ------- Utilidades ------- **/

function titulo(txt) {
  if (!txt) return "";
  return txt.slice(0,1).toUpperCase() + txt.slice(1);
}

// Fallback local: deriva datos básicos desde el ID "musculo-nivel-timestamp"
function fallbackDesdeId(id) {
  try {
    const [musculoRaw, nivelRaw] = String(id).split("-"); // ignoramos timestamp
    const musculo = (musculoRaw || "fullbody").toLowerCase();
    const nivel   = (nivelRaw || "principiante").toLowerCase();

    // Catálogo mínimo en front (coherente con el backend demo)
    const PLANES = {
      pecho:   ["Press banca 4x8–10", "Press inclinado mancuernas 3x10–12", "Aperturas 3x12–15"],
      espalda: ["Dominadas asistidas 4x6–8", "Remo con barra 4x8–10", "Jalón al pecho 3x10–12"],
      piernas: ["Sentadilla 4x6–8", "Prensa 3x10–12", "Peso muerto rumano 3x8–10"],
      hombros: ["Press militar 4x6–8", "Elevaciones laterales 3x12–15", "Pájaros 3x12–15"],
      brazos:  ["Curl barra 4x8–10", "Fondos 3x8–10", "Curl martillo 3x10–12"],
      core:    ["Plancha 3x40–60s", "Crunch 3x15–20", "Elevación de piernas 3x12–15"],
      fullbody:["Sentadilla 3x8", "Press banca 3x8", "Remo 3x8", "Peso muerto 3x5"]
    };

    const ejercicios = PLANES[musculo] || PLANES.fullbody;

    return {
      id,
      objetivo: "general",
      musculo,
      nivel,
      ejercicios,
      notas: "Ajusta volumen e intensidad según tolerancia. Hidrátate y cuida técnica."
    };
  } catch {
    return null;
  }
}
