"""Planificador de rutinas reutilizable."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import random

from .common import build_health_notes, parse_allergy_list, parse_health_flags, equip_key_norm

SCHEMES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "fuerza": {
        "principiante": {"series": (3, 4), "reps": (4, 6), "rires": "RIR 2", "rpe": "RPE 8"},
        "intermedio":   {"series": (4, 5), "reps": (3, 5), "rires": "RIR 1-2", "rpe": "RPE 8-9"},
        "avanzado":     {"series": (5, 6), "reps": (2, 4), "rires": "RIR 0-1", "rpe": "RPE 9-9.5"}
    },
    "hipertrofia": {
        "principiante": {"series": (3, 4), "reps": (8, 12), "rires": "RIR 2", "rpe": "RPE 7–8"},
        "intermedio":   {"series": (3, 5), "reps": (6, 12), "rires": "RIR 1–2", "rpe": "RPE 7–9"},
        "avanzado":     {"series": (4, 6), "reps": (6, 10), "rires": "RIR 0–1", "rpe": "RPE 8–9"}
    },
    "bajar_grasa": {
        "principiante": {"series": (3, 4), "reps": (10, 15), "rires": "RIR 2–3", "rpe": "RPE 6–7"},
        "intermedio":   {"series": (3, 4), "reps": (12, 15), "rires": "RIR 2–3", "rpe": "RPE 6–7"}
    },
    "resistencia": {
        "principiante": {"series": (3, 4), "reps": (12, 20), "rires": "RIR 2–3", "rpe": "RPE 6–7"},
        "intermedio":   {"series": (3, 4), "reps": (12, 20), "rires": "RIR 2-3", "rpe": "RPE 6-7"}
    }
}

CATALOGO: Dict[str, Dict[str, List[Tuple[str, str, str]]]] = {
    "pecho": {
        "barra": [
            ("Press banca con barra", "https://exrx.net/WeightExercises/PectoralSternal/BBBenchPress", "ExRx"),
            ("Press inclinado con barra", "https://exrx.net/WeightExercises/PectoralClavicular/BBInclineBenchPress", "ExRx"),
            ("Press cerrado (tríceps)", "https://exrx.net/WeightExercises/Triceps/BBCloseGripBenchPress", "ExRx"),
            ("Press banca con pausa", "https://exrx.net/ExInfo/TempoTraining", "ExRx"),
            ("Fondos en paralelas lastrados", "https://exrx.net/WeightExercises/PectoralSternal/ASChestDip", "ExRx"),
            ("Press en máquina Smith", "https://exrx.net/WeightExercises/PectoralSternal/SMBenchPress", "ExRx"),
            ("Press declinado con barra", "https://exrx.net/WeightExercises/PectoralSternal/BBDeclineBenchPress", "ExRx"),
            ("Remo invertido agarre ancho", "https://exrx.net/WeightExercises/TrapeziusMiddle/BBInvertedRowWide", "ExRx")
        ],
        "mancuernas": [
            ("Press banca con mancuernas", "https://exrx.net/WeightExercises/PectoralSternal/DBBenchPress", "ExRx"),
            ("Press inclinado con mancuernas", "https://exrx.net/WeightExercises/PectoralClavicular/DBInclineBenchPress", "ExRx"),
            ("Aperturas planas", "https://exrx.net/WeightExercises/PectoralSternal/DBFly", "ExRx"),
            ("Press neutro con mancuernas", "https://exrx.net/WeightExercises/PectoralSternal/DBNeutralGripBenchPress", "ExRx"),
            ("Flexiones con lastre", "https://exrx.net/WeightExercises/PectoralSternal/BWPushupWeighted", "ExRx"),
            ("Aperturas inclinadas", "https://exrx.net/WeightExercises/PectoralClavicular/DBInclineFly", "ExRx"),
            ("Cruces en polea alta", "https://exrx.net/WeightExercises/PectoralSternal/CBStandingFly", "ExRx"),
            ("Flexiones pausa 2s abajo", "https://exrx.net/ExInfo/TempoTraining", "ExRx")
        ],
        "peso_corporal": [
            ("Flexiones estándar", "https://exrx.net/WeightExercises/PectoralSternal/BWPushup", "ExRx"),
            ("Flexiones diamante", "https://exrx.net/WeightExercises/Triceps/BWCloseTricepsPushup", "ExRx"),
            ("Flexiones inclinadas", "https://exrx.net/WeightExercises/PectoralSternal/BWInclinePushup", "ExRx"),
            ("Flexiones declinadas", "https://exrx.net/WeightExercises/PectoralSternal/BWDeclinePushup", "ExRx"),
            ("Flexiones arqueadas", "https://exrx.net/WeightExercises/PectoralSternal/BWArcherPushup", "ExRx"),
            ("Fondos en paralelas", "https://exrx.net/WeightExercises/PectoralSternal/ASChestDip", "ExRx"),
            ("Plancha con toques", "https://exrx.net/WeightExercises/RectusAbdominis/BWPlank", "ExRx"),
            ("Flexiones tempo 3-1-1", "https://exrx.net/ExInfo/TempoTraining", "ExRx")
        ]
    },
    "espalda": {
        "barra": [
            ("Peso muerto convencional", "https://exrx.net/WeightExercises/ErectorSpinae/BBDeadlift", "ExRx"),
            ("Remo con barra", "https://exrx.net/WeightExercises/BackGeneral/BBBentOverRow", "ExRx"),
            ("Peso muerto rumano", "https://exrx.net/WeightExercises/Hamstrings/BBRomanianDeadlift", "ExRx"),
            ("Remo Pendlay", "https://exrx.net/WeightExercises/BackGeneral/BBPendlayRow", "ExRx"),
            ("Jalón al pecho guiado", "https://exrx.net/WeightExercises/LatissimusDorsi/LVFrontPulldown", "ExRx"),
            ("Remo T", "https://exrx.net/WeightExercises/BackGeneral/BPTBarRow", "ExRx"),
            ("Remo invertido", "https://exrx.net/WeightExercises/TrapeziusMiddle/BBInvertedRow", "ExRx"),
            ("Buenos días", "https://exrx.net/WeightExercises/ErectorSpinae/BBGoodMorning", "ExRx")
        ],
        "mancuernas": [
            ("Remo con mancuernas", "https://exrx.net/WeightExercises/BackGeneral/DBBentOverRow", "ExRx"),
            ("Remo unilateral", "https://exrx.net/WeightExercises/BackGeneral/DBOneArmRow", "ExRx"),
            ("Pull-over con mancuerna", "https://exrx.net/WeightExercises/LatissimusDorsi/DBPullover", "ExRx"),
            ("Dominadas asistidas", "https://exrx.net/WeightExercises/LatissimusDorsi/ASPullup", "ExRx"),
            ("Jalón polea agarre neutro", "https://exrx.net/WeightExercises/LatissimusDorsi/CBNeutralGripPulldown", "ExRx"),
            ("Remo pecho apoyado", "https://exrx.net/WeightExercises/BackGeneral/DBChestSupportedRow", "ExRx"),
            ("Face pull", "https://exrx.net/WeightExercises/DeltoidPosterior/CBFacePull", "ExRx"),
            ("Remo en máquina", "https://exrx.net/WeightExercises/BackGeneral/LVSeatedRow", "ExRx")
        ]
    },
    "piernas": {
        "barra": [
            ("Sentadilla trasera", "https://exrx.net/WeightExercises/Quadriceps/BBSquat", "ExRx"),
            ("Sentadilla frontal", "https://exrx.net/WeightExercises/Quadriceps/BBFrontSquat", "ExRx"),
            ("Peso muerto rumano", "https://exrx.net/WeightExercises/Hamstrings/BBRomanianDeadlift", "ExRx"),
            ("Zancadas con barra", "https://exrx.net/WeightExercises/Quadriceps/BBLunge", "ExRx"),
            ("Buenos días", "https://exrx.net/WeightExercises/ErectorSpinae/BBGoodMorning", "ExRx"),
            ("Hip thrust con barra", "https://exrx.net/WeightExercises/GluteusMaximus/BBHipThrust", "ExRx"),
            ("Sentadilla con pausa", "https://exrx.net/ExInfo/TempoTraining", "ExRx"),
            ("Sentadilla a caja", "https://exrx.net/WeightExercises/Quadriceps/BBBoxSquat", "ExRx")
        ],
        "mancuernas": [
            ("Sentadilla goblet", "https://exrx.net/WeightExercises/Quadriceps/DBGobletSquat", "ExRx"),
            ("Zancadas caminando", "https://exrx.net/WeightExercises/Quadriceps/DBLunge", "ExRx"),
            ("Peso muerto a una pierna", "https://exrx.net/WeightExercises/Hamstrings/DBSingleLegDeadlift", "ExRx"),
            ("Step-up", "https://exrx.net/WeightExercises/Quadriceps/DBStepUp", "ExRx"),
            ("Elevación de talones", "https://exrx.net/WeightExercises/Gastrocnemius/BBCalfRaise", "ExRx"),
            ("Sentadilla búlgara", "https://exrx.net/WeightExercises/Quadriceps/DBBulgarianSplitSquat", "ExRx"),
            ("Hip thrust mancuerna", "https://exrx.net/WeightExercises/GluteusMaximus/DBHipThrust", "ExRx"),
            ("Sissy squat asistida", "https://exrx.net/WeightExercises/Quadriceps/BWSissySquat", "ExRx")
        ]
    },
    "hombros": {
        "mancuernas": [
            ("Press militar mancuernas", "https://exrx.net/WeightExercises/DeltoidAnterior/DBShoulderPress", "ExRx"),
            ("Elevaciones laterales", "https://exrx.net/WeightExercises/DeltoidLateral/DBLateralRaise", "ExRx"),
            ("Pájaros (deltoide posterior)", "https://exrx.net/WeightExercises/DeltoidPosterior/DBRearDeltRaise", "ExRx"),
            ("Press Arnold", "https://exrx.net/WeightExercises/DeltoidAnterior/DBArnoldPress", "ExRx"),
            ("Elevación frontal", "https://exrx.net/WeightExercises/DeltoidAnterior/DBFrontRaise", "ExRx"),
            ("Remo al mentón moderado", "https://exrx.net/WeightExercises/TrapeziusUpper/BBUprightRow", "ExRx"),
            ("Face pull", "https://exrx.net/WeightExercises/DeltoidPosterior/CBFacePull", "ExRx"),
            ("Press en máquina", "https://exrx.net/WeightExercises/DeltoidAnterior/LVShoulderPress", "ExRx")
        ]
    },
    "brazos": {
        "mancuernas": [
            ("Curl alterno", "https://exrx.net/WeightExercises/Biceps/DBCurl", "ExRx"),
            ("Curl martillo", "https://exrx.net/WeightExercises/Brachioradialis/DBHammerCurl", "ExRx"),
            ("Curl inclinado", "https://exrx.net/WeightExercises/Biceps/DBInclineCurl", "ExRx"),
            ("Press francés mancuernas", "https://exrx.net/WeightExercises/Triceps/DBFrenchPress", "ExRx"),
            ("Extensión tríceps polea", "https://exrx.net/WeightExercises/Triceps/CBPushdown", "ExRx"),
            ("Copa tríceps", "https://exrx.net/WeightExercises/Triceps/DBOneArmOverheadExtension", "ExRx"),
            ("Curl barra Z", "https://exrx.net/WeightExercises/Biceps/BBCurl", "ExRx"),
            ("Fondos entre bancos", "https://exrx.net/WeightExercises/Triceps/BWBenchDip", "ExRx")
        ],
        "peso_corporal": [
            ("Flexiones diamante", "https://exrx.net/WeightExercises/Triceps/BWCloseTricepsPushup", "ExRx"),
            ("Fondos en paralelas", "https://exrx.net/WeightExercises/Triceps/ASDip", "ExRx"),
            ("Flexiones cerradas", "https://exrx.net/WeightExercises/Triceps/BWCloseTricepsPushup", "ExRx"),
            ("Isométrico bíceps con toalla", "https://exrx.net/ExInfo/Isometric", "ExRx"),
            ("Extensión tríceps banco", "https://exrx.net/WeightExercises/Triceps/BWBenchDip", "ExRx"),
            ("Curl con banda elástica", "https://exrx.net/WeightExercises/Biceps/CBBandCurl", "ExRx"),
            ("Press cerrado", "https://exrx.net/WeightExercises/Triceps/BBCloseGripBenchPress", "ExRx"),
            ("Flexiones tempo 3-1-1", "https://exrx.net/ExInfo/TempoTraining", "ExRx")
        ]
    },
    "core": {
        "peso_corporal": [
            ("Plancha", "https://exrx.net/WeightExercises/RectusAbdominis/BWPlank", "ExRx"),
            ("Crunch", "https://exrx.net/WeightExercises/RectusAbdominis/BWCrunch", "ExRx"),
            ("Elevación de piernas", "https://exrx.net/WeightExercises/RectusAbdominis/BWLegRaiseBentKnee", "ExRx"),
            ("Dead bug", "https://exrx.net/WeightExercises/TransverseAbdominis/BWDeadBug", "ExRx"),
            ("Pallof press (banda)", "https://exrx.net/WeightExercises/Obliques/CBBandPallofPress", "ExRx"),
            ("Plancha lateral", "https://exrx.net/WeightExercises/Obliques/BWSidePlank", "ExRx"),
            ("Mountain climbers", "https://exrx.net/WeightExercises/RectusAbdominis/BWMountainClimber", "ExRx"),
            ("Hollow hold", "https://exrx.net/WeightExercises/RectusAbdominis/BWHollowBodyHold", "ExRx")
        ]
    },
    "fullbody": {
        "mancuernas": [
            ("Sentadilla goblet", "https://exrx.net/WeightExercises/Quadriceps/DBGobletSquat", "ExRx"),
            ("Press banca mancuernas", "https://exrx.net/WeightExercises/PectoralSternal/DBBenchPress", "ExRx"),
            ("Remo con mancuernas", "https://exrx.net/WeightExercises/BackGeneral/DBBentOverRow", "ExRx"),
            ("Peso muerto rumano", "https://exrx.net/WeightExercises/Hamstrings/DBRomanianDeadlift", "ExRx"),
            ("Press militar DB", "https://exrx.net/WeightExercises/DeltoidAnterior/DBShoulderPress", "ExRx"),
            ("Zancadas", "https://exrx.net/WeightExercises/Quadriceps/DBLunge", "ExRx"),
            ("Face pull", "https://exrx.net/WeightExercises/DeltoidPosterior/CBFacePull", "ExRx"),
            ("Elevación de talones", "https://exrx.net/WeightExercises/Gastrocnemius/BBCalfRaise", "ExRx")
        ]
    },
    "cardio": {
    "peso_corporal": [
        ("Saltar la cuerda (básico)", "https://exrx.net/Aerobic/Exercises/JumpRopeSingleHop", "ExRx"),
        ("Saltar la cuerda (dobles)", "https://exrx.net/Aerobic/Exercises/JumpRopeDoubleRotation", "ExRx"),
        ("Burpees", "https://exrx.net/Aerobic/Exercises/Burpee", "ExRx"),
        ("Jumping jacks", "https://exrx.net/Aerobic/Exercises/JumpingJack", "ExRx"),
        ("Mountain climbers", "https://exrx.net/Aerobic/Exercises/MountainClimber", "ExRx"),
        ("Rodillas altas (high knees)", "https://exrx.net/Aerobic/Exercises/HighKneeRun", "ExRx"),
        ("Saltos laterales (skater)", "https://exrx.net/Plyometrics/MBLateralBound", "ExRx"),
        ("Shadow boxing (rounds)", "https://www.youtube.com/watch?v=J4j3AOVWuHE", "Tony Jeffries (YouTube)")
    ],
    "máquinas": [
        ("Cinta de correr: entrenos clave (intervalos/cuestas)", "https://www.youtube.com/watch?v=kvITDpAfJxg", "The Running Channel (YouTube)"),
        ("Cinta de correr: 20 min principiantes (intervalos guiados)", "https://www.youtube.com/watch?v=ufhM_9eLU-s", "Sam Candler (YouTube)"),
        ("Bicicleta estática: 20 min intervalos principiantes", "https://www.youtube.com/watch?v=KTQGbk8_2DM", "Sunny Health & Fitness (YouTube)"),
        ("Bicicleta estática: HIIT 15 min principiantes", "https://www.youtube.com/watch?v=GzEpFWfFWiQ", "Kaleigh Cohen Fitness (YouTube)"),
        ("Elíptica: cómo usarla (técnica)", "https://www.youtube.com/watch?v=yISC2qwdh9I", "Nuffield Health (YouTube)"),
        ("Elíptica: intervalos 10 min principiantes", "https://www.youtube.com/watch?v=t9KVWTROVb0", "Sunny Health & Fitness (YouTube)"),
        ("Remo indoor: técnica correcta", "https://www.concept2.com/training/rowing-technique", "Concept2"),
        ("Stair climber: guía para principiantes", "https://www.youtube.com/watch?v=SZU9Rm0sNOo", "Calvin The Alchemist (YouTube)")
    ]
},

}

# Esquemas de series/reps/RPE por objetivo-nivel
SCHEMES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "fuerza": {
        "principiante": {"series": (3, 4), "reps": (4, 6), "rires": "RIR 2", "rpe": "RPE 8"},
        "intermedio":   {"series": (4, 5), "reps": (3, 5), "rires": "RIR 1-2", "rpe": "RPE 8-9"},
        "avanzado":     {"series": (5, 6), "reps": (2, 4), "rires": "RIR 0-1", "rpe": "RPE 9-9.5"}
    },
    "hipertrofia": {
        "principiante": {"series": (3, 4), "reps": (8, 12), "rires": "RIR 2", "rpe": "RPE 7–8"},
        "intermedio":   {"series": (3, 5), "reps": (6, 12), "rires": "RIR 1–2", "rpe": "RPE 7–9"},
        "avanzado":     {"series": (4, 6), "reps": (6, 10), "rires": "RIR 0–1", "rpe": "RPE 8–9"}
    },
    "bajar_grasa": {
        "principiante": {"series": (3, 4), "reps": (10, 15), "rires": "RIR 2–3", "rpe": "RPE 6–7"},
        "intermedio":   {"series": (3, 4), "reps": (12, 15), "rires": "RIR 2–3", "rpe": "RPE 6–7"}
    },
    "resistencia": {
        "principiante": {"series": (3, 4), "reps": (12, 20), "rires": "RIR 2–3", "rpe": "RPE 6–7"},
        "intermedio":   {"series": (3, 4), "reps": (12, 20), "rires": "RIR 2-3", "rpe": "RPE 6-7"}
    }
}

HERO_PROGRAMS: Dict[str, Dict[str, str]] = {
    "shonen": {
        "title": "Shonen Power",
        "duration": "8 semanas",
        "focus": "Fuerza + hipertrofia con circuitos metabólicos",
        "body_type": "Atlético y veloz",
        "training": "4-5 sesiones por semana con bloques de potencia, sprints ligeros y trabajo de core avanzado.",
    },
    "ninja": {
        "title": "Ninja Agility",
        "duration": "6 semanas",
        "focus": "Movilidad, pliometría y acondicionamiento funcional",
        "body_type": "Ágil y definido",
        "training": "Sesiones cortas de alta frecuencia con énfasis en balance, saltos y control corporal.",
    },
    "mecha": {
        "title": "Mecha Endurance",
        "duration": "10 semanas",
        "focus": "Resistencia progresiva y trabajo aeróbico estructurado",
        "body_type": "Robusto y resistente",
        "training": "Ciclos largos con cardio guiado, fuerza básica y sesiones de recuperación activa.",
    },
}

DIET_BASES: Dict[str, Dict[str, Any]] = {
    "hipertrofia": {
        "calorias": "Mantenimiento + 200 kcal",
        "macros": {"proteinas": "2.0 g/kg", "carbohidratos": "5 g/kg", "grasas": "0.9 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Avena con leche descremada y frutos rojos", "Tortilla de 2 huevos + 2 claras"],
                "notes": "Agrega una fruta extra si entrenas en la manana."
            },
            {
                "name": "Almuerzo",
                "items": ["Pechuga de pollo a la plancha", "Arroz integral", "Ensalada con aceite de oliva"],
                "notes": "Incluye verduras de colores para micronutrientes."
            },
            {
                "name": "Merienda",
                "items": ["Yogur griego natural", "Nueces o mani sin sal"],
                "notes": "Ideal 90 min antes del entrenamiento."
            },
            {
                "name": "Cena",
                "items": ["Salmón u otra proteina grasa", "Batata asada", "Verduras al vapor"],
                "notes": "Añade semillas de chia o lino para omega 3."
            }
        ],
        "hydration": "2.5 L de agua con un vaso adicional por cada 20 min de entrenamiento intenso."
    },
    "fuerza": {
        "calorias": "Mantenimiento ± 0-100 kcal",
        "macros": {"proteinas": "1.8 g/kg", "carbohidratos": "4 g/kg", "grasas": "1 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Pan integral con palta", "Huevos revueltos", "Cafe sin azucar"],
                "notes": "Añade sal y potasio moderados para rendimiento."
            },
            {
                "name": "Almuerzo",
                "items": ["Carne magra", "Quinoa", "Brocoli al vapor"],
                "notes": "Utiliza hierbas en vez de salsas altas en sodio."
            },
            {
                "name": "Snack post entrenamiento",
                "items": ["Batido de proteina", "Banana"],
                "notes": "Consumir dentro de 45 min tras entrenar."
            },
            {
                "name": "Cena",
                "items": ["Pavo o tofu", "Pure de papas", "Verduras salteadas"],
                "notes": "Prioriza grasas saludables como aceite de oliva."
            }
        ],
        "hydration": "2.2 L de agua + 500 ml durante la sesion con electrolitos ligeros."
    },
    "bajar_grasa": {
        "calorias": "Déficit aproximado -300 kcal",
        "macros": {"proteinas": "2.0 g/kg", "carbohidratos": "3 g/kg", "grasas": "0.8 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Smoothie verde (espinaca, pepino, manzana)", "Yogur alto en proteina"],
                "notes": "Añade semillas para saciedad."
            },
            {
                "name": "Almuerzo",
                "items": ["Filete de pescado blanco", "Ensalada grande con legumbres"],
                "notes": "Evita aderezos con azúcar."
            },
            {
                "name": "Colacion",
                "items": ["Hummus con zanahoria y apio"],
                "notes": "Buena opcion baja en calorias y alta en fibra."
            },
            {
                "name": "Cena",
                "items": ["Wok de tofu o pollo", "Verduras salteadas", "Arroz de coliflor"],
                "notes": "Mantén las porciones controladas."
            }
        ],
        "hydration": "3.0 L de agua repartidos en el dia (apoyo a saciedad)."
    },
    "resistencia": {
        "calorias": "Mantenimiento + 100 kcal en dias de entrenamiento largo",
        "macros": {"proteinas": "1.6 g/kg", "carbohidratos": "5-7 g/kg", "grasas": "0.8 g/kg"},
        "meals": [
            {
                "name": "Desayuno pre entrenamiento",
                "items": ["Avena con banana y miel", "Bebida isotonica suave"],
                "notes": "Consumir 90 min antes de la sesion."
            },
            {
                "name": "Almuerzo",
                "items": ["Pasta integral con pollo", "Verduras salteadas"],
                "notes": "Agrega sodio controlado si sudas mucho."
            },
            {
                "name": "Snack",
                "items": ["Barra casera de avena y frutos secos"],
                "notes": "Ideal entre sesiones dobles."
            },
            {
                "name": "Cena",
                "items": ["Legumbres (lentejas/ch garbanzos)", "Ensalada variada", "Fruta"],
                "notes": "Recupera glucogeno con carbohidratos complejos."
            }
        ],
        "hydration": "Bebe 35 ml por kg de peso + reposiciona 500 ml por cada hora de cardio."
    },
    "equilibrada": {
        "calorias": "Mantenimiento",
        "macros": {"proteinas": "1.6 g/kg", "carbohidratos": "4 g/kg", "grasas": "0.9 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Yogur natural con granola", "Fruta de temporada"],
                "notes": "Incluye frutos secos si necesitas energia extra."
            },
            {
                "name": "Almuerzo",
                "items": ["Pechuga de pollo", "Arroz integral", "Ensalada de hojas"],
                "notes": "Sazona con hierbas y limon."
            },
            {
                "name": "Merienda",
                "items": ["Sandwich integral con pavo", "Verduras crudas"],
                "notes": "Buena combinacion de proteina y carbohidrato."
            },
            {
                "name": "Cena",
                "items": ["Omelette de verduras", "Pan integral o quinoa"],
                "notes": "Añade aguacate para grasas saludables."
            }
        ],
        "hydration": "2.0 L de agua al dia como base."
    }
}

# =========================================================
# Banco de ejercicios y selección
# =========================================================
def _build_bank_por_prioridad(grupo: str, equip: str) -> List[Tuple[str, str]]:
    """
    Construye un pool de ejercicios (nombre, url) según prioridad:
    1) grupo + equip
    2) grupo + cualquier equip disponible
    3) fallback: fullbody + mancuernas
    """
    g = (grupo or "").strip().lower()
    e = _equip_key_norm(equip)

    pool: List[Tuple[str, str]] = []

    # 1) grupo + equip
    if g in CATALOGO and e in CATALOGO[g]:
        pool += [(n, u) for (n, u, _src) in CATALOGO[g][e]]

    # 2) grupo + otros equip si 1) quedó corto
    if g in CATALOGO:
        for e2, lista in CATALOGO[g].items():
            if e2 == e:
                continue
            pool += [(n, u) for (n, u, _src) in lista]

    # 3) fallback adicional (se suma al final)
    if "fullbody" in CATALOGO and "mancuernas" in CATALOGO["fullbody"]:
        pool += [(n, u) for (n, u, _src) in CATALOGO["fullbody"]["mancuernas"]]

    # deduplicar por nombre
    seen = set()
    unique_pool: List[Tuple[str, str]] = []
    for n, u in pool:
        if n not in seen:
            seen.add(n)
            unique_pool.append((n, u))
    return unique_pool

def pick_exercises(grupo: str, equip: str, n: int) -> List[Tuple[str, str]]:
    """Devuelve n ejercicios (nombre, url) priorizando el banco más relevante, sin duplicados."""
    pool = _build_bank_por_prioridad(grupo, equip)
    if not pool:
        return []
    random.shuffle(pool)
    return pool[:max(0, n)]


def _build_bank_por_prioridad(grupo: str, equip: str) -> List[Tuple[str, str]]:
    """
    Construye un pool de ejercicios (nombre, url) según prioridad:
    1) grupo + equip
    2) grupo + cualquier equip disponible
    3) fallback: fullbody + mancuernas
    """
    g = (grupo or "").strip().lower()
    e = _equip_key_norm(equip)

    pool: List[Tuple[str, str]] = []

    # 1) grupo + equip
    if g in CATALOGO and e in CATALOGO[g]:
        pool += [(n, u) for (n, u, _src) in CATALOGO[g][e]]

    # 2) grupo + otros equip si 1) quedó corto
    if g in CATALOGO:
        for e2, lista in CATALOGO[g].items():
            if e2 == e:
                continue
            pool += [(n, u) for (n, u, _src) in lista]

    # 3) fallback adicional (se suma al final)
    if "fullbody" in CATALOGO and "mancuernas" in CATALOGO["fullbody"]:
        pool += [(n, u) for (n, u, _src) in CATALOGO["fullbody"]["mancuernas"]]

    # deduplicar por nombre
    seen = set()
    unique_pool: List[Tuple[str, str]] = []
    for n, u in pool:
        if n not in seen:
            seen.add(n)
            unique_pool.append((n, u))
    return unique_pool

def pick_exercises(grupo: str, equip: str, n: int) -> List[Tuple[str, str]]:
    """Devuelve n ejercicios (nombre, url) priorizando el banco más relevante, sin duplicados."""
    pool = _build_bank_por_prioridad(grupo, equip)
    if not pool:
        return []
    random.shuffle(pool)
    return pool[:max(0, n)]



def generate_workout_plan(
    *,
    objetivo: str,
    nivel: str,
    musculo: str,
    equipamiento: str,
    ejercicios_num: int,
    tiempo_min: int,
    condiciones: Optional[str] = None,
    alergias: Optional[str] = None,
    dislikes: Optional[str] = None,
    profile_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Genera un JSON estructurado de rutina y texto explicativo."""
    objetivo_norm = (objetivo or "fuerza").strip().lower()
    nivel_norm = (nivel or "intermedio").strip().lower()
    musculo_norm = (musculo or "fullbody").strip().lower()
    equip_norm = equipamiento or "mancuernas"

    plan = SCHEMES.get(objetivo_norm, {}).get(nivel_norm) or SCHEMES.get("fuerza", {}).get("intermedio")
    if not plan:
        plan = {"series": (3, 4), "reps": (8, 12), "rires": "RIR 2", "rpe": "RPE 7–8"}
    s_min, s_max = plan["series"]
    r_min, r_max = plan["reps"]
    rir_text = plan["rires"]
    rpe_text = plan["rpe"]

    health_flags = parse_health_flags(condiciones)
    health_notes = build_health_notes(health_flags)
    allergy_list = parse_allergy_list(alergias)

    if health_flags.get("hipertension") or health_flags.get("cardiaco"):
        rpe_text = "RPE <= 7"
        rir_text = "RIR 2 (evita el fallo)"
        if "Manten intensidad moderada" not in health_notes:
            health_notes.append("Manten intensidad moderada (RPE <= 7).")
    if health_flags.get("diabetes") and "Revisa glucosa" not in health_notes:
        health_notes.append("Revisa glucosa antes y despues de entrenar.")

    ejercicios = pick_exercises(musculo_norm, equip_norm, ejercicios_num)
    fallback_notice = ""
    if not ejercicios:
        ejercicios = pick_exercises("fullbody", "mancuernas", ejercicios_num)
        fallback_notice = " (fallback a fullbody por catalogo no disponible)"

    structured: List[Dict[str, Any]] = []
    bloques: List[str] = []
    for idx, (nombre, url) in enumerate(ejercicios, start=1):
        bloques.append(
            f"{idx}. {nombre} | {s_min}-{s_max} series x {r_min}-{r_max} reps | {rpe_text} | {rir_text} | Video: {url}"
        )
        structured.append(
            {
                "orden": idx,
                "nombre": nombre,
                "video": url,
                "series": f"{s_min}-{s_max}",
                "repeticiones": f"{r_min}-{r_max}",
                "rpe": rpe_text,
                "rir": rir_text,
            }
        )

    routine_id = f"rutina-{int(datetime.now().timestamp())}"
    header_lines: List[str] = [
        f"Rutina - {musculo_norm.title()} - nivel {nivel_norm} - objetivo {objetivo_norm}{fallback_notice}",
        f"Sesion aproximada {tiempo_min} min | {ejercicios_num} ejercicios | Equipo: {equip_norm}",
        f"Progresion sugerida: +2.5-5% carga o +1 rep/serie manteniendo {rir_text}.",
    ]
    if profile_data:
        profile_bits: List[str] = []
        weight = profile_data.get("weight_kg")
        height = profile_data.get("height_cm")
        goal = profile_data.get("primary_goal")
        activity = profile_data.get("activity_level")
        if weight:
            profile_bits.append(f"Peso: {weight} kg")
        if height:
            profile_bits.append(f"Altura: {height} cm")
        if goal:
            profile_bits.append(f"Objetivo declarado: {str(goal).replace('_', ' ')}")
        if activity:
            profile_bits.append(f"Actividad: {activity}")
        if profile_bits:
            header_lines.append("Datos perfil: " + " | ".join(profile_bits))
    if health_notes or allergy_list:
        extra_bits: List[str] = []
        if health_notes:
            extra_bits.append("; ".join(health_notes))
        if allergy_list:
            extra_bits.append("Alergias registradas: " + ", ".join(allergy_list))
        header_lines.append("Precaucion salud: " + " | ".join(extra_bits))

    header = "\n".join(header_lines)
    texto = header + (
        "\n\n" + "\n".join(bloques) if bloques else "\n\n(No se encontraron ejercicios en el catalogo.)"
    )

    explanation = {
        "datos_usados": {
            "objetivo": objetivo_norm,
            "nivel": nivel_norm,
            "musculo": musculo_norm,
            "equipamiento": equip_norm,
            "tiempo_min": tiempo_min,
            "ejercicios": ejercicios_num,
            "profile": profile_data or {},
            "condiciones": condiciones,
            "alergias": alergias,
        },
        "criterios": [
            "Series/repeticiones basadas en esquema objetivo-nivel.",
            "Ejercicios seleccionados del catalogo priorizando grupo y equipamiento.",
            "Progresion propuesta con sobrecarga gradual.",
        ],
        "reglas": [
            "Ajustes aplicados por banderas de salud." if health_flags else "Sin restricciones medicas adicionales.",
            "Se consideraron alergias registradas." if allergy_list else "Sin alergias declaradas.",
        ],
        "fuentes": ["Catálogo interno (ExRx y recursos validados)."],
    }

    routine_summary = {
        "type": "routine_detail",
        "routine_id": routine_id,
        "header": header_lines[0],
        "summary": {
            "tiempo_min": tiempo_min,
            "ejercicios": ejercicios_num,
            "equipamiento": equip_norm,
            "objetivo": objetivo_norm,
            "nivel": nivel_norm,
            "musculo": musculo_norm,
            "fallback": bool(fallback_notice.strip()),
            "progresion": f"+2.5-5% carga o +1 rep/serie manteniendo {rir_text}.",
            "health_notes": health_notes or None,
            "allergies": allergy_list or None,
            "medical_conditions": condiciones if condiciones and condiciones.lower() not in {"", "ninguna", "ninguno", "no"} else None,
        },
        "fallback_notice": fallback_notice.strip() or None,
        "exercises": structured,
        "explanation": explanation,
    }

    context_payload: Dict[str, Any] = {}
    for key, value in (
        ("medical_conditions", condiciones),
        ("allergies", alergias),
        ("dislikes", dislikes),
    ):
        if value and str(value).strip().lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload[key] = value

    return {
        "text": texto,
        "routine_summary": routine_summary,
        "context_payload": context_payload,
    }
