import React, { useState } from "react";
import { useLocale } from "../contexts/LocaleContext";
import { useAuth } from "../contexts/AuthContext";
import { API } from "../services/apijs";
import "../styles/entrenos-unicos.css";

export default function EntrenosUnicos() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();
  const [selectedPreview, setSelectedPreview] = useState(null);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusError, setStatusError] = useState("");
  const [savedPlan, setSavedPlan] = useState(null);

  const handleScrollToPlans = () => {
    const target = document.getElementById("planes-disponibles");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const handleEnrollPlan = async (plan) => {
    if (!plan) return;
    setStatusMessage("");
    setStatusError("");
    setSavedPlan(null);
    if (!isAuthenticated) {
      setStatusError("Inicia sesión para recibir el plan en tu perfil.");
      return;
    }
    try {
      const details = planDetails[plan.key] || {};
      const workoutPlan = getWorkoutPlan(plan.key);
      const response = await API.profile.heroPlans.create({
        plan_key: plan.key,
        title: plan.title,
        payload: {
          plan_key: plan.key,
          title: plan.title,
          duration: plan.duration,
          focus: details.focus || plan.description,
          body_type: plan.bodyType,
          training: details.training,
          diet: details.diet,
          calories: details.calories,
          macros: details.macros,
          meals: details.meals,
          sources: details.sources,
          guidelines: details.guidelines,
          progression_model: getProgressionModel(plan.key),
          workout_plan: workoutPlan,
        },
        source: "web",
      });
      setSavedPlan(response?.plan || null);
      setStatusMessage("Plan guardado en tu perfil. Puedes verlo en tu cuenta.");
    } catch (err) {
      setStatusError(err?.message || "No pude guardar el plan. Intentalo otra vez.");
    }
  };

  const handleDownload = async (planId) => {
    if (!planId) return;
    setStatusError("");
    try {
      const rawBase = import.meta.env.VITE_API_BASE_URL || "";
      const BASE = rawBase && rawBase !== "/" ? rawBase.replace(/\/+$/, "") : "";
      const resp = await fetch(`${BASE}/profile/hero-plans/${planId}/pdf`, { credentials: "include" });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `entreno_unico_${planId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setStatusError(err?.message || "No pude descargar el plan.");
    }
  };

  const getPlanByIndex = (idx) => plans[(idx + plans.length) % plans.length];
  const handlePrevPlan = () => setCarouselIndex((prev) => (prev - 1 + plans.length) % plans.length);
  const handleNextPlan = () => setCarouselIndex((prev) => (prev + 1) % plans.length);

  const progressionModels = {
    flash: "Doble progresion en compuestos (sube repeticiones y luego carga), con descarga ligera cada 4 semanas.",
    shazam: "Primero calidad tecnica, luego volumen y por ultimo intensidad en saltos/velocidad.",
    mecha: "Aumenta tiempo de trabajo o distancia semanalmente, manteniendo una sesion de descarga cada 5 semanas.",
    batman_bale: "Bloques de 4 semanas: acumulacion (8-12 reps), intensificacion (4-6 reps), peaking (3-5 reps).",
    batman_affleck: "Ondulacion semanal de cargas: pesado/medio/volumen para sostener fuerza e hipertrofia.",
    batman_pattinson: "Progresion por densidad: mismo trabajo en menos tiempo y luego mayor dificultad tecnica.",
    capitan_america_evans: "Split de alto volumen con sobrecarga progresiva semanal en los basicos.",
    superman_cavill: "Fase 1 fuerza base, fase 2 hipertrofia, fase 3 acondicionamiento metabolico.",
    superman_corenswet: "Empuje-traccion-piernas con subida progresiva de tonelaje y mini-deload cada 6 semanas.",
    wolverine_jackman: "Periodizacion de repeticiones (12-10-8-6-5) y ajustes de cardio segun definicion.",
  };

  const workoutPlanTemplates = {
    flash: [
      {
        day: "Dia 1 - Potencia de pierna",
        objective: "Fuerza de tren inferior y salida explosiva",
        exercises: [
          { name: "Back Squat", sets: "5", reps: "5", intensity: "RPE 8", rest: "120 s" },
          { name: "Romanian Deadlift", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Box Jump", sets: "5", reps: "3", intensity: "Explosivo", rest: "75 s" },
          { name: "Sled Push", sets: "6", reps: "20 m", intensity: "Alto", rest: "90 s" },
          { name: "Plank + Dead Bug", sets: "3", reps: "45 s + 10/10", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 2 - Torso de potencia",
        objective: "Empuje/traccion con velocidad",
        exercises: [
          { name: "Bench Press", sets: "5", reps: "4", intensity: "RPE 8", rest: "120 s" },
          { name: "Weighted Pull-up", sets: "4", reps: "6", intensity: "RPE 8", rest: "120 s" },
          { name: "Push Press", sets: "4", reps: "5", intensity: "RPE 8", rest: "90 s" },
          { name: "Medicine Ball Slam", sets: "4", reps: "10", intensity: "Explosivo", rest: "60 s" },
          { name: "Pallof Press", sets: "3", reps: "12/12", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 3 - Metabolico completo",
        objective: "Acondicionamiento y potencia metabolica",
        exercises: [
          { name: "Thruster", sets: "5", reps: "8", intensity: "RPE 8", rest: "75 s" },
          { name: "Kettlebell Swing", sets: "5", reps: "15", intensity: "RPE 8", rest: "60 s" },
          { name: "Burpee Over Bar", sets: "4", reps: "10", intensity: "Alto", rest: "60 s" },
          { name: "Farmer Carry", sets: "4", reps: "30 m", intensity: "RPE 8", rest: "75 s" },
        ],
      },
      {
        day: "Dia 4 - Velocidad y core",
        objective: "Sprint y estabilidad central",
        exercises: [
          { name: "Sprint", sets: "8", reps: "20 s", intensity: "90-95%", rest: "90 s" },
          { name: "Walking Lunge", sets: "3", reps: "12/12", intensity: "RPE 7", rest: "75 s" },
          { name: "TRX Row", sets: "4", reps: "12", intensity: "RPE 7", rest: "60 s" },
          { name: "Hanging Knee Raise", sets: "4", reps: "12", intensity: "Control", rest: "45 s" },
        ],
      },
    ],
    shazam: [
      {
        day: "Dia 1 - Movilidad + agilidad",
        objective: "Rango articular y cambios de direccion",
        exercises: [
          { name: "Mobility Flow (cadera/tobillo/torax)", sets: "3", reps: "8 min", intensity: "Suave", rest: "30 s" },
          { name: "Ladder Drills", sets: "8", reps: "20 s", intensity: "Rapido", rest: "40 s" },
          { name: "Lateral Bounds", sets: "4", reps: "8/8", intensity: "Explosivo", rest: "60 s" },
          { name: "Bear Crawl", sets: "4", reps: "20 m", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 2 - Plyo de cuerpo completo",
        objective: "Elasticidad y potencia",
        exercises: [
          { name: "Depth Jump", sets: "5", reps: "3", intensity: "Max calidad", rest: "90 s" },
          { name: "Broad Jump", sets: "5", reps: "4", intensity: "Explosivo", rest: "75 s" },
          { name: "Explosive Push-up", sets: "4", reps: "6", intensity: "RPE 8", rest: "75 s" },
          { name: "Battle Rope Intervals", sets: "8", reps: "20 s", intensity: "Alto", rest: "40 s" },
        ],
      },
      {
        day: "Dia 3 - Core reactivo",
        objective: "Estabilidad dinamica",
        exercises: [
          { name: "Turkish Get-up", sets: "4", reps: "4/4", intensity: "Tecnico", rest: "60 s" },
          { name: "Single Leg RDL", sets: "4", reps: "10/10", intensity: "RPE 7", rest: "60 s" },
          { name: "Plank Reach", sets: "3", reps: "12/12", intensity: "Control", rest: "45 s" },
          { name: "Side Plank with Hip Lift", sets: "3", reps: "12/12", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 4 - Condicionamiento funcional",
        objective: "Capacidad aerobica sin perder agilidad",
        exercises: [
          { name: "Shadow Boxing", sets: "6", reps: "2 min", intensity: "Moderado", rest: "45 s" },
          { name: "Skater Jump", sets: "4", reps: "12/12", intensity: "RPE 8", rest: "60 s" },
          { name: "Row Erg", sets: "6", reps: "250 m", intensity: "Fuerte", rest: "60 s" },
          { name: "Hollow Body Hold", sets: "4", reps: "30 s", intensity: "Control", rest: "40 s" },
        ],
      },
    ],
    mecha: [
      {
        day: "Dia 1 - Fuerza base",
        objective: "Base robusta de tren inferior y espalda",
        exercises: [
          { name: "Trap Bar Deadlift", sets: "5", reps: "5", intensity: "RPE 8", rest: "150 s" },
          { name: "Front Squat", sets: "4", reps: "6", intensity: "RPE 8", rest: "120 s" },
          { name: "Barbell Row", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Farmer Carry", sets: "5", reps: "30 m", intensity: "Pesado", rest: "90 s" },
        ],
      },
      {
        day: "Dia 2 - Cardio progresivo",
        objective: "Resistencia aerobia",
        exercises: [
          { name: "Zone 2 Run", sets: "1", reps: "35-50 min", intensity: "Suave", rest: "-" },
          { name: "Assault Bike", sets: "6", reps: "2 min", intensity: "Moderado", rest: "60 s" },
          { name: "Sled Drag", sets: "6", reps: "25 m", intensity: "RPE 8", rest: "75 s" },
        ],
      },
      {
        day: "Dia 3 - Hero WOD",
        objective: "Resistencia muscular y mental",
        exercises: [
          { name: "EMOM 24' - KB Swing", sets: "8", reps: "12", intensity: "RPE 7-8", rest: "-" },
          { name: "EMOM 24' - Push-up", sets: "8", reps: "15", intensity: "RPE 7-8", rest: "-" },
          { name: "EMOM 24' - Walking Lunge", sets: "8", reps: "20 pasos", intensity: "RPE 7-8", rest: "-" },
          { name: "Row Cooldown", sets: "1", reps: "10 min", intensity: "Suave", rest: "-" },
        ],
      },
      {
        day: "Dia 4 - Torso resistente",
        objective: "Fuerza de empuje/traccion bajo fatiga",
        exercises: [
          { name: "Incline Bench Press", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Weighted Pull-up", sets: "4", reps: "6", intensity: "RPE 8", rest: "90 s" },
          { name: "Landmine Press", sets: "4", reps: "10/10", intensity: "RPE 7", rest: "60 s" },
          { name: "Plank Walkout", sets: "3", reps: "10", intensity: "Control", rest: "45 s" },
        ],
      },
    ],
    batman_bale: [
      {
        day: "Dia 1 - Golden 5 (pierna)",
        objective: "Fuerza pesada en basicos",
        exercises: [
          { name: "Back Squat", sets: "5", reps: "5", intensity: "RPE 8", rest: "150 s" },
          { name: "Romanian Deadlift", sets: "4", reps: "8", intensity: "RPE 8", rest: "120 s" },
          { name: "Bulgarian Split Squat", sets: "3", reps: "10/10", intensity: "RPE 8", rest: "75 s" },
          { name: "Ab Wheel", sets: "4", reps: "10", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 2 - Golden 5 (pecho/espalda)",
        objective: "Torso denso",
        exercises: [
          { name: "Bench Press", sets: "5", reps: "5", intensity: "RPE 8", rest: "150 s" },
          { name: "Weighted Chin-up", sets: "5", reps: "5", intensity: "RPE 8", rest: "120 s" },
          { name: "Dumbbell Row", sets: "4", reps: "10", intensity: "RPE 8", rest: "75 s" },
          { name: "Dips", sets: "4", reps: "8-12", intensity: "RPE 8", rest: "60 s" },
        ],
      },
      {
        day: "Dia 3 - Funcional combate",
        objective: "Acondicionamiento y transferencia",
        exercises: [
          { name: "Heavy Bag Intervals", sets: "10", reps: "1 min", intensity: "Alto", rest: "30 s" },
          { name: "Kettlebell Clean & Press", sets: "4", reps: "8/8", intensity: "RPE 8", rest: "75 s" },
          { name: "Sled Push", sets: "6", reps: "20 m", intensity: "Fuerte", rest: "75 s" },
          { name: "Hanging Leg Raise", sets: "4", reps: "12", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 4 - Hombro y brazo",
        objective: "Detalle estetico",
        exercises: [
          { name: "Overhead Press", sets: "5", reps: "5", intensity: "RPE 8", rest: "120 s" },
          { name: "Lateral Raise", sets: "4", reps: "15", intensity: "RPE 8", rest: "45 s" },
          { name: "Barbell Curl", sets: "4", reps: "10", intensity: "RPE 8", rest: "60 s" },
          { name: "Skull Crusher", sets: "4", reps: "10", intensity: "RPE 8", rest: "60 s" },
        ],
      },
    ],
    batman_affleck: [
      {
        day: "Dia 1 - Pecho/Espalda pesado",
        objective: "Fuerza maxima de torso",
        exercises: [
          { name: "Bench Press", sets: "6", reps: "4", intensity: "RPE 9", rest: "150 s" },
          { name: "Weighted Pull-up", sets: "5", reps: "5", intensity: "RPE 8.5", rest: "120 s" },
          { name: "Incline Dumbbell Press", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Chest Supported Row", sets: "4", reps: "10", intensity: "RPE 8", rest: "75 s" },
        ],
      },
      {
        day: "Dia 2 - Pierna densa",
        objective: "Masa y potencia",
        exercises: [
          { name: "Back Squat", sets: "5", reps: "5", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Leg Press", sets: "4", reps: "12", intensity: "RPE 9", rest: "90 s" },
          { name: "Romanian Deadlift", sets: "4", reps: "8", intensity: "RPE 8", rest: "120 s" },
          { name: "Walking Lunge", sets: "3", reps: "12/12", intensity: "RPE 8", rest: "75 s" },
        ],
      },
      {
        day: "Dia 3 - Chaos conditioning",
        objective: "Capacidad anaerobica",
        exercises: [
          { name: "Airdyne Sprint", sets: "12", reps: "15 s", intensity: "All out", rest: "45 s" },
          { name: "Battle Rope", sets: "8", reps: "30 s", intensity: "Alto", rest: "30 s" },
          { name: "Sledgehammer Strike", sets: "6", reps: "15/15", intensity: "Alto", rest: "45 s" },
          { name: "Suitcase Carry", sets: "4", reps: "25 m/25 m", intensity: "RPE 8", rest: "60 s" },
        ],
      },
      {
        day: "Dia 4 - Hombro y brazo pesado",
        objective: "Densidad de hombro",
        exercises: [
          { name: "Push Press", sets: "5", reps: "4", intensity: "RPE 8.5", rest: "120 s" },
          { name: "Upright Row", sets: "4", reps: "10", intensity: "RPE 8", rest: "75 s" },
          { name: "Close Grip Bench Press", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Hammer Curl", sets: "4", reps: "10", intensity: "RPE 8", rest: "60 s" },
        ],
      },
    ],
    batman_pattinson: [
      {
        day: "Dia 1 - Calistenia fuerte",
        objective: "Fuerza relativa",
        exercises: [
          { name: "Pull-up", sets: "5", reps: "AMRAP tecnico", intensity: "RIR 1-2", rest: "90 s" },
          { name: "Push-up", sets: "5", reps: "15-25", intensity: "RIR 2", rest: "60 s" },
          { name: "Ring Row", sets: "4", reps: "12", intensity: "RPE 8", rest: "60 s" },
          { name: "Pistol Squat (asistida)", sets: "4", reps: "8/8", intensity: "RPE 8", rest: "75 s" },
        ],
      },
      {
        day: "Dia 2 - Boxeo + core",
        objective: "Resistencia y coordinacion",
        exercises: [
          { name: "Shadow Boxing", sets: "8", reps: "2 min", intensity: "Moderado-alto", rest: "45 s" },
          { name: "Heavy Bag", sets: "6", reps: "2 min", intensity: "Alto", rest: "60 s" },
          { name: "Jump Rope", sets: "8", reps: "1 min", intensity: "Rapido", rest: "30 s" },
          { name: "Hollow Hold + Russian Twist", sets: "4", reps: "30 s + 20", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 3 - Funcional",
        objective: "Agilidad y control",
        exercises: [
          { name: "Sandbag Clean", sets: "5", reps: "6", intensity: "RPE 8", rest: "75 s" },
          { name: "Kettlebell Snatch", sets: "4", reps: "8/8", intensity: "RPE 8", rest: "75 s" },
          { name: "Box Step-up", sets: "4", reps: "12/12", intensity: "RPE 7", rest: "60 s" },
          { name: "Bear Crawl", sets: "4", reps: "20 m", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 4 - Cardio base",
        objective: "Definicion sin perder rendimiento",
        exercises: [
          { name: "Run Intervals", sets: "10", reps: "1 min", intensity: "RPE 8", rest: "1 min" },
          { name: "Assault Bike", sets: "6", reps: "2 min", intensity: "Moderado", rest: "1 min" },
          { name: "Mobility Flow", sets: "1", reps: "15 min", intensity: "Suave", rest: "-" },
        ],
      },
    ],
    capitan_america_evans: [
      {
        day: "Dia 1 - Torso fuerza",
        objective: "Compuestos pesados",
        exercises: [
          { name: "Bench Press", sets: "5", reps: "5", intensity: "RPE 8", rest: "150 s" },
          { name: "Pendlay Row", sets: "5", reps: "6", intensity: "RPE 8", rest: "120 s" },
          { name: "Weighted Dip", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Weighted Pull-up", sets: "4", reps: "6", intensity: "RPE 8", rest: "90 s" },
        ],
      },
      {
        day: "Dia 2 - Pierna fuerza",
        objective: "Masa y estabilidad",
        exercises: [
          { name: "Back Squat", sets: "5", reps: "5", intensity: "RPE 8", rest: "150 s" },
          { name: "Deadlift", sets: "4", reps: "4", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Rear Foot Elevated Split Squat", sets: "4", reps: "10/10", intensity: "RPE 8", rest: "75 s" },
          { name: "Standing Calf Raise", sets: "4", reps: "15", intensity: "RPE 8", rest: "45 s" },
        ],
      },
      {
        day: "Dia 3 - Torso hipertrofia",
        objective: "Volumen y detalle",
        exercises: [
          { name: "Incline Dumbbell Press", sets: "4", reps: "10", intensity: "RPE 8", rest: "90 s" },
          { name: "Seated Cable Row", sets: "4", reps: "12", intensity: "RPE 8", rest: "75 s" },
          { name: "Lateral Raise", sets: "4", reps: "15", intensity: "RPE 8", rest: "45 s" },
          { name: "Face Pull", sets: "4", reps: "15", intensity: "RPE 8", rest: "45 s" },
        ],
      },
      {
        day: "Dia 4 - Potencia + core",
        objective: "Atletismo global",
        exercises: [
          { name: "Power Clean", sets: "5", reps: "3", intensity: "RPE 8", rest: "120 s" },
          { name: "Sled Push", sets: "6", reps: "20 m", intensity: "Fuerte", rest: "75 s" },
          { name: "Battle Rope", sets: "8", reps: "30 s", intensity: "Alto", rest: "30 s" },
          { name: "Hanging Leg Raise", sets: "4", reps: "12", intensity: "Control", rest: "45 s" },
        ],
      },
    ],
    superman_cavill: [
      {
        day: "Dia 1 - Fuerza maxima",
        objective: "Construir base de fuerza",
        exercises: [
          { name: "Back Squat", sets: "6", reps: "3", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Bench Press", sets: "6", reps: "3", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Weighted Chin-up", sets: "5", reps: "5", intensity: "RPE 8", rest: "120 s" },
          { name: "Farmer Carry", sets: "5", reps: "30 m", intensity: "Pesado", rest: "90 s" },
        ],
      },
      {
        day: "Dia 2 - Volumen hipertrofia",
        objective: "Pecho/hombro dominante",
        exercises: [
          { name: "Incline Bench Press", sets: "5", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Overhead Press", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Lat Pulldown", sets: "4", reps: "10", intensity: "RPE 8", rest: "75 s" },
          { name: "Cable Fly", sets: "4", reps: "12", intensity: "RPE 8", rest: "60 s" },
        ],
      },
      {
        day: "Dia 3 - Pierna y posterior",
        objective: "Pierna potente",
        exercises: [
          { name: "Deadlift", sets: "5", reps: "4", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Front Squat", sets: "4", reps: "6", intensity: "RPE 8", rest: "120 s" },
          { name: "Hip Thrust", sets: "4", reps: "10", intensity: "RPE 8", rest: "90 s" },
          { name: "Hamstring Curl", sets: "4", reps: "12", intensity: "RPE 8", rest: "60 s" },
        ],
      },
      {
        day: "Dia 4 - Circuito intenso",
        objective: "Definicion y condicion",
        exercises: [
          { name: "Row Erg", sets: "6", reps: "500 m", intensity: "RPE 8", rest: "75 s" },
          { name: "Burpee", sets: "5", reps: "12", intensity: "Alto", rest: "45 s" },
          { name: "Kettlebell Swing", sets: "5", reps: "20", intensity: "RPE 8", rest: "45 s" },
          { name: "Ab Wheel", sets: "4", reps: "12", intensity: "Control", rest: "45 s" },
        ],
      },
    ],
    superman_corenswet: [
      {
        day: "Dia 1 - Push",
        objective: "Pecho/hombro/triceps",
        exercises: [
          { name: "Bench Press", sets: "5", reps: "6", intensity: "RPE 8", rest: "120 s" },
          { name: "Incline Dumbbell Press", sets: "4", reps: "10", intensity: "RPE 8", rest: "90 s" },
          { name: "Seated Dumbbell Press", sets: "4", reps: "10", intensity: "RPE 8", rest: "75 s" },
          { name: "Cable Lateral Raise", sets: "4", reps: "15", intensity: "RPE 8", rest: "45 s" },
          { name: "Triceps Pressdown", sets: "4", reps: "12", intensity: "RPE 8", rest: "45 s" },
        ],
      },
      {
        day: "Dia 2 - Pull",
        objective: "Espalda/biceps",
        exercises: [
          { name: "Deadlift", sets: "5", reps: "5", intensity: "RPE 8", rest: "150 s" },
          { name: "Weighted Pull-up", sets: "4", reps: "6", intensity: "RPE 8", rest: "120 s" },
          { name: "Barbell Row", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Seated Row", sets: "4", reps: "12", intensity: "RPE 8", rest: "75 s" },
          { name: "EZ Curl", sets: "4", reps: "10", intensity: "RPE 8", rest: "60 s" },
        ],
      },
      {
        day: "Dia 3 - Piernas",
        objective: "Masa de tren inferior",
        exercises: [
          { name: "Back Squat", sets: "5", reps: "6", intensity: "RPE 8", rest: "120 s" },
          { name: "Leg Press", sets: "4", reps: "12", intensity: "RPE 9", rest: "90 s" },
          { name: "Romanian Deadlift", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
          { name: "Leg Curl", sets: "4", reps: "12", intensity: "RPE 8", rest: "60 s" },
          { name: "Standing Calf Raise", sets: "5", reps: "15", intensity: "RPE 8", rest: "45 s" },
        ],
      },
      {
        day: "Dia 4 - Push/Pull accesorio",
        objective: "Volumen extra",
        exercises: [
          { name: "Dip", sets: "4", reps: "8-12", intensity: "RPE 8", rest: "75 s" },
          { name: "Lat Pulldown", sets: "4", reps: "10", intensity: "RPE 8", rest: "75 s" },
          { name: "Machine Chest Press", sets: "4", reps: "12", intensity: "RPE 8", rest: "60 s" },
          { name: "Face Pull", sets: "4", reps: "15", intensity: "RPE 8", rest: "45 s" },
          { name: "Cable Curl + Rope Extension", sets: "3", reps: "12 + 12", intensity: "RPE 8", rest: "45 s" },
        ],
      },
    ],
    wolverine_jackman: [
      {
        day: "Dia 1 - Fuerza torso",
        objective: "Basicos pesados",
        exercises: [
          { name: "Bench Press", sets: "5", reps: "5", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Weighted Chin-up", sets: "5", reps: "5", intensity: "RPE 8.5", rest: "120 s" },
          { name: "Overhead Press", sets: "4", reps: "6", intensity: "RPE 8", rest: "90 s" },
          { name: "Barbell Row", sets: "4", reps: "8", intensity: "RPE 8", rest: "90 s" },
        ],
      },
      {
        day: "Dia 2 - Fuerza pierna",
        objective: "Compuestos pesados de pierna",
        exercises: [
          { name: "Back Squat", sets: "5", reps: "5", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Deadlift", sets: "4", reps: "4", intensity: "RPE 8.5", rest: "150 s" },
          { name: "Walking Lunge", sets: "4", reps: "10/10", intensity: "RPE 8", rest: "75 s" },
          { name: "Hanging Leg Raise", sets: "4", reps: "12", intensity: "Control", rest: "45 s" },
        ],
      },
      {
        day: "Dia 3 - Hipertrofia",
        objective: "Volumen muscular",
        exercises: [
          { name: "Incline Dumbbell Press", sets: "4", reps: "10-12", intensity: "RPE 8", rest: "75 s" },
          { name: "Lat Pulldown", sets: "4", reps: "10-12", intensity: "RPE 8", rest: "75 s" },
          { name: "Leg Press", sets: "4", reps: "12", intensity: "RPE 8", rest: "90 s" },
          { name: "Seated Curl + Skull Crusher", sets: "3", reps: "12 + 12", intensity: "RPE 8", rest: "45 s" },
        ],
      },
      {
        day: "Dia 4 - Definicion",
        objective: "Mantener masa y reducir grasa",
        exercises: [
          { name: "HIIT Treadmill", sets: "12", reps: "30 s", intensity: "90%", rest: "60 s" },
          { name: "Kettlebell Swing", sets: "5", reps: "15", intensity: "RPE 8", rest: "45 s" },
          { name: "Battle Rope", sets: "8", reps: "20 s", intensity: "Alto", rest: "40 s" },
          { name: "Core Circuit (Plank/Side/Hollow)", sets: "4", reps: "40 s c/u", intensity: "Control", rest: "45 s" },
        ],
      },
    ],
  };

  const getWorkoutPlan = (planKey) => workoutPlanTemplates[planKey] || [];
  const getProgressionModel = (planKey) => progressionModels[planKey] || "Ajusta cargas o volumen cada semana y manten tecnica estricta.";

  const planDetails = {
    flash: {
      focus: "Fuerza e hipertrofia con circuitos metabólicos",
      training: "4-5 sesiones/semana con compuestos, bloques de potencia y core.",
      diet: "Superavit moderado con proteínas magras y carbohidratos complejos.",
      calories: "Ajuste según peso y objetivo.",
      macros: "Proteína 1.6-2.2 g/kg, carbos altos, grasas moderadas.",
      meals: [
        "Avena con claras y fruta",
        "Pollo con arroz integral y verduras",
        "Batido de proteína post-entreno",
      ],
      sources: [],
      guidelines: [
        "Calienta 8-10 min y prioriza técnica.",
        "Progresión semanal de cargas o repeticiones.",
        "Descanso 60-90 s en accesorios y 2-3 min en compuestos.",
      ],
    },
    shazam: {
      focus: "Movilidad, pliometría y acondicionamiento funcional",
      training: "4 sesiones/semana con drills de agilidad, saltos y core reactivo.",
      diet: "Mantenimiento con proteína alta y carbos alrededor del entreno.",
      calories: "Mantenimiento calórico.",
      macros: "Proteína alta, carbos moderados, grasas estables.",
      meals: [
        "Huevos con avena y fruta",
        "Pescado con quinoa y verduras",
        "Yogur griego con frutos secos",
      ],
      sources: [],
      guidelines: [
        "Enfoca calidad de movimiento antes de velocidad.",
        "Incluye movilidad diaria 10-15 min.",
        "Recuperación activa 1-2 días por semana.",
      ],
    },
    mecha: {
      focus: "Resistencia progresiva y trabajo aeróbico estructurado",
      training: "4-5 sesiones/semana con cardio guiado y fuerza base.",
      diet: "Mantenimiento o leve superávit con carbos para energía.",
      calories: "Ajuste según demanda de cardio.",
      macros: "Proteína 1.6-2.0 g/kg, carbos altos, grasas moderadas.",
      meals: [
        "Tostadas integrales con huevos",
        "Carne magra con batata",
        "Snack de frutos secos",
      ],
      sources: [],
      guidelines: [
        "No saltes las sesiones de cardio progresivo.",
        "Prioriza hidratación y electrolitos.",
        "Mantén 7-8 h de sueño para recuperación.",
      ],
    },
    batman_bale: {
      focus: "Fuerza + volumen con base en compuestos",
      training: "Compuestos tipo press banca, sentadilla y peso muerto con trabajo funcional.",
      diet: "Fase de aumento agresivo y luego dieta limpia hipercalórica.",
      calories: "No especificadas; aumento agresivo al inicio.",
      macros: "No especificadas; prioridad a proteína magra y carbos complejos.",
      meals: [
        "Avena con batido de proteína",
        "Salmón con arroz y batata",
        "Pasta integral con proteína magra",
      ],
      sources: [
        "https://www.gq.com.mx/entretenimiento/articulo/christian-bale-rutinas-de-ejercicio-en-su-carrera",
        "https://steelsupplements.com/blogs/steel-blog/christian-bales-batman-workout-routine-and-diet-plan",
        "https://forums.superherohype.com/threads/bales-diet-and-training-for-bb.311673/",
      ],
      guidelines: [
        "Prioriza los compuestos y sube cargas gradualmente.",
        "Agrega 2 bloques de acondicionamiento por semana.",
        "Evita entrenar al fallo en todas las series.",
      ],
    },
    batman_affleck: {
      focus: "Hipertrofia con énfasis en fuerza máxima",
      training: "Cargas altas con volumen estilo culturismo y circuitos de acondicionamiento.",
      diet: "Dieta six-pack, sin lácteos, 6 comidas diarias y control de sodio.",
      calories: "3500-4000 kcal/día",
      macros: "Proteína alta, carbos complejos moderados, grasas saludables.",
      meals: [
        "Claras con avena y banana",
        "Pechuga de pollo con camote",
        "Salmón con brócoli",
      ],
      sources: [
        "https://manofmany.com/culture/fitness/ben-affleck-batman-workout-diet-plan",
      ],
      guidelines: [
        "Entrena 5-6 días con cargas altas.",
        "Controla sodio y evita alcohol.",
        "Incluye circuitos cortos de acondicionamiento.",
      ],
    },
    batman_pattinson: {
      focus: "Fuerza relativa y acondicionamiento funcional",
      training: "Calistenia, cardio y boxeo con trabajo de core.",
      diet: "Mantenimiento o ligero déficit con proteína alta.",
      calories: "~2800 kcal/día",
      macros: "Proteína 200-220 g/día; carbos fibrosos; grasas moderadas.",
      meals: [
        "Avena con huevo cocido",
        "Atún con tortitas de arroz",
        "Filete magro con arroz y vegetales",
      ],
      sources: [
        "https://manofmany.com/culture/fitness/robert-pattinson-batman-workout-diet-plan",
        "https://www.menshealth.com/fitness/a39367846/robert-pattinson-batman-diet-plan-aseel-soueid/",
      ],
      guidelines: [
        "Prioriza movilidad y cardio 3-4 veces por semana.",
        "Busca funcionalidad antes que volumen.",
        "Core diario de 10-15 min.",
      ],
    },
    capitan_america_evans: {
      focus: "Hipertrofia total y fuerza con alto volumen",
      training: "Split torso-pierna con compuestos pesados y trabajo de core.",
      diet: "Superávit moderado-alto con comidas frecuentes.",
      calories: "~4000 kcal/día",
      macros: "Proteína 200-240 g/día; carbos altos; grasas saludables.",
      meals: [
        "Avena con frutas y nueces",
        "Ensalada de pollo con arroz integral",
        "Caseína antes de dormir",
      ],
      sources: [
        "https://manofmany.com/culture/fitness/chris-evans-captain-america-workout-diet-plan",
        "https://www.gq.com.mx/cuidados/fitness/articulos/rutina-de-ejercicio-de-chris-evans/3021",
      ],
      guidelines: [
        "Come cada 2-3 horas en fase de volumen.",
        "No descuides tren inferior.",
        "Suma movimientos gimnásticos para estabilidad.",
      ],
    },
    superman_cavill: {
      focus: "Hipertrofia + fuerza con alto volumen",
      training: "Fases de fuerza máxima y luego circuitos intensos.",
      diet: "Fase de volumen hipercalórica y ajuste a alimentos más magros.",
      calories: "~5000 kcal/día (volumen)",
      macros: "Proteína ~300 g/día; carbos altos; grasas saludables.",
      meals: [
        "5 claras + 2 yemas + filete",
        "Curry de pollo con arroz jazmín",
        "Batido de caseína nocturno",
      ],
      sources: [
        "http://abcnews.go.com/blogs/entertainment/2013/06/henry-cavill-made-enormous-changes-using-man-of-steel-workout",
        "https://manofmany.com/culture/fitness/henry-cavills-superman-diet-workout-plan",
      ],
      guidelines: [
        "Volumen alto con control de grasa.",
        "Cardio ligero en ayunas en fase de definición.",
        "Recuperación estricta y sueño 8 h.",
      ],
    },
    superman_corenswet: {
      focus: "Volumen con sobrecarga progresiva",
      training: "Split empuje-tracción-piernas con progresión semanal.",
      diet: "Volumen limpio con 5 comidas y 2 batidos hipercalóricos.",
      calories: "4500-6000 kcal/día",
      macros: "Proteína ~250 g/día; carbos abundantes; grasas moderadas.",
      meals: [
        "4 huevos + avena con mantequilla de maní",
        "Pollo con arroz",
        "Batido hipercalórico",
      ],
      sources: [
        "https://www.gq.com/story/david-corenswet-superman-legacy-workout-1",
        "https://www.eonline.com/news/1419758/supermans-david-corenswet-details-diet-and-workout-transformation",
        "https://menshealth.com.au/david-corenswet-workout-routine-diet-plan/",
        "https://www.eatingwell.com/david-corenswet-weight-gain-for-superman-11769355",
      ],
      guidelines: [
        "Progresión semanal de cargas o repeticiones.",
        "Prioriza técnica y rango completo.",
        "Recuperación activa 1 día por semana.",
      ],
    },
    wolverine_jackman: {
      focus: "Fuerza + hipertrofia con periodización",
      training: "Básicos pesados con progresión y bloques 4x10-12 a 4x5.",
      diet: "Ayuno 16/8 con ingesta calórica alta en ventana.",
      calories: "~4000 kcal/día (volumen)",
      macros: "230 g proteína / 230 g carbohidratos / 230 g grasas aprox.",
      meals: [
        "Avena con arándanos y 2 huevos",
        "Filete magro + batata + brócoli",
        "Pescado blanco con aguacate",
      ],
      sources: [
        "https://www.businessinsider.com/how-hugh-jackman-got-in-shape-for-logan-2017-3",
        "https://www.businessinsider.com/4000-calorie-diet-hugh-jackman-get-shredded-to-play-wolverine-2020-7",
      ],
      guidelines: [
        "Periodiza cargas cada 3-4 semanas.",
        "Incluye HIIT moderado en definición.",
        "Controla hidratación antes de sesiones exigentes.",
      ],
    },
  };

  const plans = [
    {
      key: "flash",
      title: 'Flash',
      duration: '8 semanas',
      description: 'Enfocado en fuerza e hipertrofia con circuitos metabólicos.',
      img: '/flash.jpg',
      bodyType: 'Atlético y veloz',
      exclusiveNotes: [
        'Incluye complejos de potencia y circuitos metabólicos que solo se habilitan con la inscripción al programa.',
        'En rutinas generales se puede rescatar 1-2 movimientos (ej. contrastes o sprints) pero no el bloque completo.',
        'Pensado para quienes buscan el físico atlético con alto volumen de potencia.'
      ],
    },
    {
      key: "shazam",
      title: 'Shazam',
      duration: '6 semanas',
      description: 'Enfocado en movilidad, plyometrics y acondicionamiento.',
      img: '/shazam.jpg',
      bodyType: 'Ágil y definido',
      exclusiveNotes: [
        'Acceso a módulos de parkour-lite, pliometría avanzada y sesiones de agilidad que no se publican fuera del programa.',
        'Para rutinas estándar solo se permite tomar 1-2 drills como complemento; la progresión completa es exclusiva.',
        'Ideal para trabajar coordinación, core reactivo y definición con enfoque ninja.'
      ],
    },
    {
      key: "mecha",
      title: 'Bane',
      duration: '10 semanas',
      description: 'Enfocado en resistencia y trabajo aeróbico progresivo.',
      img: '/bane.jpg',
      bodyType: 'Robusto y resistente',
      exclusiveNotes: [
        'Integra bloques de strongman, sled drags y hero WODs diseñados solo para quienes se inscriben en el plan.',
        'Las rutinas generales solo pueden reutilizar 1-2 ejercicios pesados como inspiración, no la estructura completa.',
        'Construye la base robusta y resistente que ves en el render del plan.'
      ],
    },
    {
      key: "batman_bale",
      title: "Batman (Christian Bale)",
      duration: "12 semanas",
      description: "Fuerza y volumen con compuestos pesados y acondicionamiento funcional.",
      img: "/batman-bale.jpg",
      bodyType: "Atlético y marcado",
      exclusiveNotes: [
        "Incluye bloques de fuerza tipo 'golden 5' y trabajo funcional inspirado en artes marciales.",
        "Solo se libera el esquema completo con fases de volumen y definición dentro del plan.",
        "Pensado para construir torso amplio con cintura compacta.",
      ],
    },
    {
      key: "batman_affleck",
      title: "Batman (Ben Affleck)",
      duration: "12 semanas",
      description: "Hipertrofia con énfasis en fuerza máxima y densidad muscular.",
      img: "/batman-affleck.jpg",
      bodyType: "Masivo y denso",
      exclusiveNotes: [
        "Programa de cargas altas con bloques de volumen y fuerza para espalda, pecho y hombros.",
        "Incluye sesiones tipo chaos training y circuitos de acondicionamiento pesado.",
        "No se publica fuera del plan el protocolo de volumen completo.",
      ],
    },
    {
      key: "batman_pattinson",
      title: "Batman (Robert Pattinson)",
      duration: "8 semanas",
      description: "Fuerza relativa, movilidad y acondicionamiento funcional.",
      img: "/batman-pattinson.jpg",
      bodyType: "Fibroso y ágil",
      exclusiveNotes: [
        "Integra boxeo, cardio y calistenia con sacos de arena para look definido.",
        "Las rutinas generales solo muestran una parte del circuito funcional.",
        "Ideal si buscas agilidad y resistencia con bajo volumen.",
      ],
    },
    {
      key: "capitan_america_evans",
      title: "Capitán América (Chris Evans)",
      duration: "12 semanas",
      description: "Hipertrofia total y fuerza con alto volumen.",
      img: "/cap-am-chris.jpg",
      bodyType: "Musculoso y equilibrado",
      exclusiveNotes: [
        "Split torso-pierna con sobrecarga progresiva y trabajo de core frecuente.",
        "Incluye fases de potencia y ejercicios gimnásticos avanzados.",
        "Acceso completo solo desde la inscripción al plan.",
      ],
    },
    {
      key: "superman_cavill",
      title: "Superman (Henry Cavill)",
      duration: "12 semanas",
      description: "Volumen alto con fases de fuerza y acondicionamiento intenso.",
      img: "/superman-henry.jpg",
      bodyType: "Masivo y definido",
      exclusiveNotes: [
        "Incluye fases de hipertrofia y circuitos de alta intensidad para definición.",
        "Se libera el plan de volumen y el ajuste final solo en el programa.",
        "Pensado para un físico dominante en pecho y hombros.",
      ],
    },
    {
      key: "superman_corenswet",
      title: "Superman (David Corenswet)",
      duration: "20 semanas",
      description: "Volumen con sobrecarga progresiva y división empuje-tracción-piernas.",
      img: "/superman-david.jpg",
      bodyType: "Muy masivo",
      exclusiveNotes: [
        "Plan de ganancia muscular controlada con progresión semanal.",
        "Incluye ejemplos de comidas hipercalóricas y calendario de fases.",
        "La guía completa solo está disponible dentro del plan.",
      ],
    },
    {
      key: "wolverine_jackman",
      title: "Wolverine (Hugh Jackman)",
      duration: "12 semanas",
      description: "Fuerza máxima con periodización y definición avanzada.",
      img: "/wolverine-hugh.jpg",
      bodyType: "Muy musculoso y definido",
      exclusiveNotes: [
        "Bloques 4x10-12 a 4x5 y trabajo funcional para escenas de combate.",
        "Incluye ventana de nutrición tipo 16/8 para fases específicas.",
        "Rutina completa disponible solo para inscritos.",
      ],
    },
  ];

  return (
    <main className="profile-page entrenos-page">
      <div className="profile-shell">
        <header className="profile-header text-center mb-4">
          <h1 className="profile-title">Entrenos únicos</h1>
          <h4 className="profile-subtitle">
            Duración definida, guía nutricional e instrucciones generales para lograr físicos icónicos.
          </h4>
          <div className="entrenos-hero-actions">
            <button className="btn btn-primary" onClick={handleScrollToPlans}>Explorar planes</button>
            <a className="btn btn-outline-secondary" href="/registro">Inscribirme</a>
          </div>
        </header>
        <div className="profile-highlight mb-4 entrenos-pad-left">
          <div>
            <h2 className="profile-highlight-title">Acceso y seguimiento</h2>
            <p className="mb-0">Guarda tu plan y revísalo desde tu perfil cuando quieras.</p>
          </div>
          <div className="profile-highlight-icon" aria-hidden="true">
            <span className="bi bi-lightning-charge" />
          </div>
        </div>

        <section className="mb-4 entrenos-pad-left" id="planes-disponibles">
          <h2 className="mb-2">Planes disponibles</h2>
          <p className="text-muted">Explora los planes en el carrusel y previsualiza el estilo antes de inscribirte.</p>
          {(statusMessage || statusError) && (
            <div className="entrenos-alerts">
              {statusMessage && <div className="alert alert-success">{statusMessage}</div>}
              {statusError && <div className="alert alert-danger">{statusError}</div>}
            </div>
          )}
          <div className="entrenos-carousel">
            <button className="entrenos-carousel-btn" onClick={handlePrevPlan} aria-label="Plan anterior">
              ‹
            </button>
            <div className="entrenos-carousel-track">
              {[-1, 0, 1].map((offset) => {
                const plan = getPlanByIndex(carouselIndex + offset);
                const isCenter = offset === 0;
                return (
                  <article
                    className={`entreno-card entreno-card--carousel ${isCenter ? "is-center" : ""} ${selectedPreview === plan.key ? "is-selected" : ""}`}
                    key={`${plan.key}-${offset}`}
                    role="button"
                    onClick={() => setSelectedPreview(plan.key)}
                  >
                    <div className="entreno-card-image">
                      <img src={plan.img} alt={`${plan.title} preview`} />
                    </div>
                    <div className="entreno-card-body">
                      <div className="entreno-card-meta">
                        <span>{plan.duration}</span>
                        <span>{plan.bodyType}</span>
                      </div>
                      <h3>{plan.title}</h3>
                      <p className="entreno-card-desc">{plan.description}</p>
                    </div>
                    <div className="entreno-card-footer">
                      <button className={`btn ${selectedPreview === plan.key ? "btn-outline-primary" : "btn-primary"}`} onClick={(e) => { e.stopPropagation(); setSelectedPreview(plan.key); }}>
                        {selectedPreview === plan.key ? "Seleccionado" : "Ver vista"}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
            <button className="entrenos-carousel-btn" onClick={handleNextPlan} aria-label="Plan siguiente">
              ›
            </button>
          </div>

          <div className="entreno-preview mt-4">
            <h3 className="h5">Vista previa seleccionada</h3>
            {!selectedPreview && <p className="text-muted">Haz clic en una tarjeta para ver una vista ampliada del tipo de cuerpo asociado al plan.</p>}
            {selectedPreview && (
              (() => {
                const p = plans.find(pl => pl.key === selectedPreview);
                const details = planDetails[p?.key] || {};
                const workoutPlan = getWorkoutPlan(p?.key);
                const progressionModel = getProgressionModel(p?.key);
                return (
                  <div className="card shadow-sm border-0">
                    <div className="row g-0">
                      <div className="col-md-5">
                        <img src={p.img} alt={`${p.title} large preview`} className="img-fluid h-100 w-100" style={{ objectFit: "cover" }} />
                      </div>
                      <div className="col-md-7">
                        <div className="card-body">
                          <h4 className="card-title">{p.title} — {p.duration}</h4>
                          <p className="card-text">{p.description}</p>
                          <p className="card-text"><strong>Tipo de cuerpo objetivo:</strong> {p.bodyType}</p>
                          <div className="entreno-preview-details">
                            <div>
                              <strong>Entrenamiento:</strong>
                              <p className="mb-2">{details.training || "Consulta la guía completa del plan para el detalle."}</p>
                            </div>
                            <div>
                              <strong>Nutrición:</strong>
                              <p className="mb-2">{details.diet || "Incluye guía de macros y ejemplo de comidas."}</p>
                            </div>
                            {details.calories && <p className="mb-2"><strong>Calorías:</strong> {details.calories}</p>}
                            {details.macros && <p className="mb-2"><strong>Macros:</strong> {details.macros}</p>}
                            {(details.meals || []).length > 0 && (
                              <div className="mb-2">
                                <strong>Ejemplos de comidas:</strong>
                                <ul className="mb-0">
                                  {details.meals.map((meal) => (
                                    <li key={`${p.key}-meal-${meal}`}>{meal}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {(details.guidelines || []).length > 0 && (
                              <div>
                                <strong>Instrucciones generales:</strong>
                                <ul className="mb-0">
                                  {details.guidelines.map((note) => (
                                    <li key={`${p.key}-guide-${note}`}>{note}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {workoutPlan.length > 0 && (
                              <div className="mt-3">
                                <strong>Plan de ejercicios sugerido:</strong>
                                <ul className="mb-2">
                                  {workoutPlan.map((session) => (
                                    <li key={`${p.key}-${session.day}`}>
                                      <strong>{session.day}:</strong> {session.objective}
                                      <ul>
                                        {session.exercises.slice(0, 3).map((exercise) => (
                                          <li key={`${p.key}-${session.day}-${exercise.name}`}>
                                            {exercise.name} — {exercise.sets}x{exercise.reps} ({exercise.intensity})
                                          </li>
                                        ))}
                                      </ul>
                                    </li>
                                  ))}
                                </ul>
                                <p className="mb-0"><strong>Progresión:</strong> {progressionModel}</p>
                              </div>
                            )}
                          </div>
                          <p className="text-muted">Selecciona este estilo si te identifica el tipo de cuerpo mostrado y tus objetivos.</p>
                          <div className="d-flex flex-wrap gap-2">
                            <button className="btn btn-primary" onClick={() => handleEnrollPlan(p)}>Recibir plan</button>
                            {!isAuthenticated && <a className="btn btn-outline-secondary" href="/registro">Registrarme</a>}
                            {savedPlan?.id && savedPlan?.plan_key === p.key && (
                              <button className="btn btn-outline-primary" onClick={() => handleDownload(savedPlan.id)}>Descargar PDF</button>
                            )}
                            <button className="btn btn-outline-secondary" onClick={() => setSelectedPreview(null)}>Cerrar vista</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
