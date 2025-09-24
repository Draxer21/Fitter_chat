// src/pages/RutinaPage.jsx
import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";

export default function RutinaPage() {
  const { id: rawId } = useParams();
  const id = decodeURIComponent(String(rawId || ""));
  const [loading, setLoading] = useState(true);
  const [rutina, setRutina] = useState(null);
  const [error, setError] = useState(null);
  const [usandoFallback, setUsandoFallback] = useState(false);
  const abortRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    // cancela petición previa si cambia el id
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    (async () => {
      setLoading(true);
      setError(null);
      setUsandoFallback(false);

      try {
        const res = await fetch(`/chat/routine/${encodeURIComponent(id)}`, {
          signal: controller.signal
        });
        if (cancelled) return;

        if (res.ok) {
          const data = await res.json();
          // defensa: validamos forma mínima
          const sane = saneaRutina(data) || fallbackDesdeId(id);
          setRutina(sane);
          setUsandoFallback(!saneaRutina(data));
        } else {
          setRutina(fallbackDesdeId(id));
          setUsandoFallback(true);
        }
      } catch (e) {
        if (e?.name !== "AbortError") {
          setError("No se pudo obtener la rutina desde el backend.");
          // Aún así mostramos algo al usuario
          setRutina(fallbackDesdeId(id));
          setUsandoFallback(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [id]);

  if (loading) {
    return <main style={{ padding: 24 }}>Cargando rutina…</main>;
  }

  if (!rutina) {
    return <main style={{ padding: 24 }}>No se encontró la rutina.</main>;
  }

  const { objetivo, musculo, nivel, ejercicios = [], notas } = rutina;

  return (
    <main style={{ padding: 24, maxWidth: 840, margin: "0 auto" }}>
      <header style={{ marginBottom: 16 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600 }}>
          Rutina: {titulo(musculo)} · {nivel}
        </h1>
        <p style={{ color: "#555" }}>
          Objetivo: <strong>{objetivo}</strong>
        </p>
        <p style={{ color: "#777" }}>ID: {id}</p>

        {usandoFallback && (
          <div
            role="status"
            style={{
              marginTop: 8,
              padding: "6px 10px",
              border: "1px solid #fde68a",
              background: "#fffbeb",
              color: "#92400e",
              borderRadius: 8
            }}
          >
            Mostrando rutina generada localmente (fallback). Cuando expongas
            <code> /chat/routine/:id</code> desde Flask, se cargará la versión del backend.
          </div>
        )}

        {error && (
          <div
            role="alert"
            style={{
              marginTop: 8,
              padding: "6px 10px",
              border: "1px solid #fecaca",
              background: "#fee2e2",
              color: "#991b1b",
              borderRadius: 8
            }}
          >
            {error}
          </div>
        )}
      </header>

      <section
        style={{
          background: "#fafafa",
          padding: 16,
          borderRadius: 12,
          border: "1px solid #eee"
        }}
      >
        <h2 style={{ marginBottom: 8, fontSize: 18, fontWeight: 600 }}>
          Bloques de ejercicio
        </h2>
        <ol style={{ paddingLeft: 18, lineHeight: 1.7 }}>
          {ejercicios.map((e, idx) => (
            <li key={idx}>{e}</li>
          ))}
        </ol>

        {notas && (
          <>
            <h3 style={{ marginTop: 16, marginBottom: 6, fontWeight: 600 }}>
              Notas
            </h3>
            <p>{notas}</p>
          </>
        )}
      </section>

      <footer style={{ marginTop: 20, display: "flex", gap: 8 }}>
        <Link
          to="/"
          style={{
            padding: "8px 12px",
            border: "1px solid #ccc",
            borderRadius: 8,
            textDecoration: "none",
            color: "#111"
          }}
        >
          Volver al chat
        </Link>
        <button
          onClick={() => window.print()}
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            background: "#0d6efd",
            color: "white",
            border: "none",
            cursor: "pointer"
          }}
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
  return txt.slice(0, 1).toUpperCase() + txt.slice(1);
}

function saneaRutina(raw) {
  if (!raw || typeof raw !== "object") return null;
  const objetivo = pickStr(raw.objetivo, "general");
  const musculo = pickStr(raw.musculo, "fullbody");
  const nivel = pickStr(raw.nivel, "principiante");
  const ejercicios = Array.isArray(raw.ejercicios)
    ? raw.ejercicios.filter(Boolean)
    : [];
  const notas =
    typeof raw.notas === "string" && raw.notas.trim() ? raw.notas : undefined;

  if (!objetivo || !musculo || !nivel) return null;
  if (ejercicios.length === 0) return null;

  return { objetivo, musculo, nivel, ejercicios, notas };
}

function pickStr(v, d) {
  return typeof v === "string" && v.trim() ? v.trim() : d;
}

// Fallback local: deriva datos básicos desde el ID "musculo-nivel-timestamp"
function fallbackDesdeId(id) {
  try {
    const parts = String(id).split("-");
    const musculoRaw = parts.shift();
    const nivelRaw = parts.shift();
    const musculo = (musculoRaw || "fullbody").toLowerCase();
    const nivel = (nivelRaw || "principiante").toLowerCase();

    // Catálogo mínimo en front (coherente con backend demo)
    const PLANES = {
      pecho: ["Press banca 4x8–10", "Press inclinado mancuernas 3x10–12", "Aperturas 3x12–15"],
      espalda: ["Dominadas asistidas 4x6–8", "Remo con barra 4x8–10", "Jalón al pecho 3x10–12"],
      piernas: ["Sentadilla 4x6–8", "Prensa 3x10–12", "Peso muerto rumano 3x8–10"],
      hombros: ["Press militar 4x6–8", "Elevaciones laterales 3x12–15", "Pájaros 3x12–15"],
      brazos: ["Curl barra 4x8–10", "Fondos 3x8–10", "Curl martillo 3x10–12"],
      core: ["Plancha 3x40–60s", "Crunch 3x15–20", "Elevación de piernas 3x12–15"],
      fullbody: ["Sentadilla 3x8", "Press banca 3x8", "Remo 3x8", "Peso muerto 3x5"]
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
