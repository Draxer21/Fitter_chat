"""LLM orchestration layer with tool-calling and lightweight RAG.

This module centralizes the conversational flow for /chat by:
- Preparing system and context prompts that emphasize Datos/Criterios/Reglas/Fuentes.
- Exposing a tool catalog (planner, RAG, guardrails) usable by native tool-calling models.
- Running a minimal retrieval-augmented search over project docs and policies.
- Applying guardrails (screen_user, validate_plan) before returning responses.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from flask import current_app

from .context_manager import ChatContextManager
from .errors import ChatServiceError
from ..planner import diets as diet_planner
from ..planner import workouts as workout_planner
from ..planner.common import build_health_notes, parse_health_flags

# Lazy imports to keep startup fast
try:  # pragma: no cover - optional dependency
    from openai import AzureOpenAI, OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None
    AzureOpenAI = None

try:  # pragma: no cover - optional dependency
    import chromadb  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    chromadb = None
    embedding_functions = None


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: str
    base_url: str
    temperature: float
    max_tokens: int
    embeddings_model: str
    rag_max_results: int
    rag_index_path: str


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap if end - overlap > start else end
    return chunks


def format_explanation_block(payload: Dict[str, Any]) -> str:
    datos = payload.get("datos_usados") or payload.get("datos") or {}
    criterios = payload.get("criterios") or []
    reglas = payload.get("reglas") or []
    fuentes = payload.get("fuentes") or []

    def _fmt_dict(d: Dict[str, Any]) -> str:
        if not d:
            return "-"
        return "; ".join([f"{k}: {v}" for k, v in d.items() if v not in (None, "", [], {})]) or "-"

    def _fmt_list(values: Iterable[Any]) -> str:
        items = []
        for v in values:
            if isinstance(v, dict):
                items.append(_fmt_dict(v))
            elif v is None:
                continue
            else:
                items.append(str(v))
        return "; ".join(items) if items else "-"

    return (
        "Datos usados: "
        + _fmt_dict(datos)
        + "\nCriterios: "
        + _fmt_list(criterios)
        + "\nReglas: "
        + _fmt_list(reglas)
        + "\nFuentes: "
        + _fmt_list(fuentes)
    )


class KnowledgeStore:
    """Minimal RAG over docs/, policies and catalog files."""

    def __init__(self, base_dir: str, settings: LLMSettings, logger) -> None:
        self.base_dir = base_dir
        self.settings = settings
        self.logger = logger
        self._client = None
        self._collection = None
        self._fallback_corpus: List[Tuple[str, str]] = []  # (source, text)
        self._ready = False

    @property
    def enabled(self) -> bool:
        return chromadb is not None and self.settings.api_key

    def _embedding_function(self):
        if not embedding_functions:
            return None
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.settings.api_key, model_name=self.settings.embeddings_model
        )

    def _iter_sources(self) -> List[Tuple[str, str]]:
        sources: List[Tuple[str, str]] = []
        docs_dir = os.path.join(self.base_dir, "docs")
        frontend_access = os.path.join(self.base_dir, "frontend", "ACCESIBILIDAD.md")
        data_dir = os.path.join(self.base_dir, "backend", "data")

        # docs and policies
        for root in (docs_dir, os.path.join(docs_dir, "policies")):
            if not os.path.isdir(root):
                continue
            for name in os.listdir(root):
                path = os.path.join(root, name)
                if os.path.isfile(path):
                    sources.append((path, path))

        if os.path.isfile(frontend_access):
            sources.append((frontend_access, frontend_access))

        if os.path.isdir(data_dir):
            for name in os.listdir(data_dir):
                if name.endswith(".json"):
                    path = os.path.join(data_dir, name)
                    sources.append((path, path))

        return sources

    def _load_documents(self) -> List[Tuple[str, str]]:
        loaded: List[Tuple[str, str]] = []
        for display, path in self._iter_sources():
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                if text:
                    # Avoid huge catalog payloads; cap to 40k chars
                    trimmed = text[:40000]
                    loaded.append((display, trimmed))
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("No se pudo leer %s para el indice RAG: %s", path, exc)
        return loaded

    def build(self) -> None:
        if self._ready:
            return

        docs = self._load_documents()
        if not docs:
            return
        self._fallback_corpus = list(docs)

        if not self.enabled:
            self._ready = True
            return

        try:
            os.makedirs(self.settings.rag_index_path, exist_ok=True)
        except Exception:
            pass
        client = chromadb.PersistentClient(path=self.settings.rag_index_path) if self.settings.rag_index_path else chromadb.Client()  # type: ignore
        emb_fn = self._embedding_function()
        self._collection = client.get_or_create_collection("fitter-kb", embedding_function=emb_fn)

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for idx, (source, text) in enumerate(docs):
            for chunk_idx, chunk in enumerate(_chunk_text(text)):
                ids.append(f"doc-{idx}-{chunk_idx}")
                documents.append(chunk)
                metadatas.append({"source": source, "chunk": chunk_idx})
        if documents:
            self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        self._ready = True

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []
        self.build()

        if self.enabled:
            try:
                if not self._collection:
                    return []
                result = self._collection.query(
                    query_texts=[query],
                    n_results=min(self.settings.rag_max_results, 6),
                )
                matches: List[Dict[str, Any]] = []
                ids = result.get("ids", [[]])[0]
                docs = result.get("documents", [[]])[0]
                metas = result.get("metadatas", [[]])[0]
                dists = result.get("distances", [[]])[0]
                for doc, meta, dist in zip(docs, metas, dists):
                    matches.append(
                        {
                            "text": doc,
                            "source": (meta or {}).get("source"),
                            "score": dist,
                        }
                    )
                return matches
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Busqueda RAG fallo, se usa fallback: %s", exc)

        # fallback: naive keyword scan
        scored: List[Tuple[float, Dict[str, Any]]] = []
        lowered = query.lower()
        for source, text in self._fallback_corpus:
            if not text:
                continue
            score = text.lower().count(lowered)
            if score:
                scored.append((float(score), {"text": text[:600], "source": source, "score": score}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[: self.settings.rag_max_results]]


class ToolCatalog:
    def __init__(self, kb: KnowledgeStore, format_explanation: Callable[[Dict[str, Any]], str]) -> None:
        self.kb = kb
        self.format_explanation = format_explanation

    def schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_workout_plan",
                    "description": "Genera una rutina de entrenamiento con series/reps y enlaces a ejercicios.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "objetivo": {"type": "string"},
                            "nivel": {"type": "string"},
                            "musculo": {"type": "string"},
                            "equipamiento": {"type": "string"},
                            "ejercicios_num": {"type": "integer"},
                            "tiempo_min": {"type": "integer"},
                            "condiciones": {"type": "string"},
                            "alergias": {"type": "string"},
                            "dislikes": {"type": "string"},
                        },
                        "required": ["objetivo", "nivel", "musculo", "equipamiento", "ejercicios_num", "tiempo_min"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_meal_plan",
                    "description": "Genera un plan de comidas/dieta estructurado.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "objetivo": {"type": "string"},
                            "nivel": {"type": "string"},
                            "alergias": {"type": "string"},
                            "dislikes": {"type": "string"},
                            "condiciones": {"type": "string"},
                        },
                        "required": ["objetivo", "nivel"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "log_progress",
                    "description": "Registra progreso o notas del usuario (peso, reps, sintomas).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric": {"type": "string"},
                            "value": {"type": "string"},
                            "note": {"type": "string"},
                        },
                        "required": ["metric"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_kb",
                    "description": "Busca en politicas, docs y catalogos para responder con fuentes citables.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Pregunta del usuario."}
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "screen_user",
                    "description": "Evalua banderas rojas de salud antes de recomendar planes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "medical_conditions": {"type": "string"},
                            "symptoms": {"type": "string"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_plan",
                    "description": "Valida que el plan generado incluya explicacion y campos requeridos.",
                    "parameters": {
                        "type": "object",
                        "properties": {"plan": {"type": "object"}},
                        "required": ["plan"],
                    },
                },
            },
        ]

    def dispatch(self, name: str, args: Dict[str, Any], manager: ChatContextManager) -> Dict[str, Any]:
        name = (name or "").strip()
        if name == "generate_workout_plan":
            return self._do_workout(args, manager)
        if name == "generate_meal_plan":
            return self._do_meal(args, manager)
        if name == "log_progress":
            return self._do_log_progress(args, manager)
        if name == "search_kb":
            return self._do_search_kb(args)
        if name == "screen_user":
            return self._do_screen_user(args, manager)
        if name == "validate_plan":
            return self._do_validate_plan(args)
        raise ChatServiceError(f"Tool no soportada: {name}")

    def _do_workout(self, args: Dict[str, Any], manager: ChatContextManager) -> Dict[str, Any]:
        ctx = manager.context
        payload = workout_planner.generate_workout_plan(
            objetivo=args.get("objetivo") or "fuerza",
            nivel=args.get("nivel") or "intermedio",
            musculo=args.get("musculo") or "fullbody",
            equipamiento=args.get("equipamiento") or "mancuernas",
            ejercicios_num=int(args.get("ejercicios_num") or 5),
            tiempo_min=int(args.get("tiempo_min") or 40),
            condiciones=args.get("condiciones") or ctx.medical_conditions,
            alergias=args.get("alergias") or ctx.allergies,
            dislikes=args.get("dislikes") or ctx.dislikes,
            profile_data=None,
        )

        context_payload = payload.get("context_payload") or {}
        self._apply_context_updates(context_payload, manager)

        routine_summary = payload.get("routine_summary") or {}
        explanation_dict = routine_summary.get("explanation") or {}
        routine_summary["explanation_text"] = self.format_explanation(explanation_dict) if explanation_dict else None

        response = {
            "text": payload.get("text"),
            "custom": routine_summary,
        }
        validation = self._do_validate_plan({"plan": routine_summary})
        if validation.get("warnings"):
            response.setdefault("custom", {})["validation_warnings"] = validation["warnings"]
        return {"result": payload, "responses": [response]}

    def _do_meal(self, args: Dict[str, Any], manager: ChatContextManager) -> Dict[str, Any]:
        ctx = manager.context
        payload = diet_planner.generate_diet_plan(
            objetivo=args.get("objetivo") or "equilibrada",
            nivel=args.get("nivel") or "intermedio",
            alergias=args.get("alergias") or ctx.allergies,
            dislikes=args.get("dislikes") or ctx.dislikes,
            condiciones=args.get("condiciones") or ctx.medical_conditions,
            profile_data=None,
        )

        context_payload = payload.get("context_payload") or {}
        self._apply_context_updates(context_payload, manager)

        diet_payload = payload.get("diet_payload") or {}
        explanation_dict = diet_payload.get("explanation") or {}
        diet_payload["explanation_text"] = self.format_explanation(explanation_dict) if explanation_dict else None

        response = {
            "text": payload.get("text"),
            "custom": diet_payload,
        }
        validation = self._do_validate_plan({"plan": diet_payload})
        if validation.get("warnings"):
            response.setdefault("custom", {})["validation_warnings"] = validation["warnings"]
        return {"result": payload, "responses": [response]}

    def _do_log_progress(self, args: Dict[str, Any], manager: ChatContextManager) -> Dict[str, Any]:
        entry = {
            "type": "progress_log",
            "metric": args.get("metric"),
            "value": args.get("value"),
            "note": args.get("note"),
        }
        try:
            manager.add_history_entry(entry)
        except Exception:
            pass
        explanation = {
            "datos_usados": {"metric": args.get("metric"), "value": args.get("value")},
            "criterios": ["Se registra texto libre solicitado por el usuario."],
            "reglas": ["No se modifica salud ni se recomiendan medicamentos."],
            "fuentes": ["Entrada directa del usuario."],
        }
        response = {
            "text": "Registro anotado. Puedo usarlo para ajustar proximas recomendaciones.",
            "custom": {
                "type": "note",
                "data": entry,
                "explanation": self.format_explanation(explanation),
            },
        }
        return {"result": entry, "responses": [response]}

    def _do_search_kb(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query") or ""
        matches = self.kb.search(query)
        return {"result": matches, "responses": []}

    def _do_screen_user(self, args: Dict[str, Any], manager: ChatContextManager) -> Dict[str, Any]:
        conditions = args.get("medical_conditions") or manager.context.medical_conditions or ""
        symptoms = args.get("symptoms") or ""
        combined = "; ".join([conditions, symptoms]).strip()
        flags = parse_health_flags(combined)
        notes = build_health_notes(flags)
        red_flags = []
        if "dolor" in combined.lower() or "pecho" in combined.lower():
            red_flags.append("Dolor toracico reportado. Derivar a medico.")
        if flags.get("cardiaco"):
            red_flags.append("Antecedentes cardiacos: usar intensidad moderada y validacion medica previa.")
        needs_clearance = bool(red_flags)
        explanation = self.format_explanation(
            {
                "datos_usados": {"condiciones": combined},
                "criterios": ["Revision de palabras clave de riesgo."],
                "reglas": ["Escalar a profesional si hay banderas rojas."],
                "fuentes": ["OMS actividad fisica 2020", "Guia MINSAL 2023"],
            }
        )
        response = {
            "text": (
                "Detecte posibles banderas rojas, recomiendo consultar con un profesional antes de seguir." if needs_clearance else "Sin banderas rojas críticas detectadas."
            ),
            "custom": {
                "type": "screening",
                "flags": red_flags or None,
                "notes": notes or None,
                "explanation": explanation,
            },
        }
        return {"result": {"needs_clearance": needs_clearance, "flags": red_flags, "notes": notes}, "responses": [response]}

    def _do_validate_plan(self, args: Dict[str, Any]) -> Dict[str, Any]:
        plan = args.get("plan") or {}
        warnings: List[str] = []
        if not isinstance(plan, dict):
            warnings.append("Plan no estructurado.")
        if "explanation" not in plan:
            warnings.append("El plan no incluye bloque de explicacion.")
        if plan.get("type") not in {"routine_detail", "diet_plan", "note", "assistant_message"}:
            warnings.append("Falta tipo de plan reconocido.")
        return {"result": {"ok": not warnings}, "warnings": warnings, "responses": []}

    def _apply_context_updates(self, payload: Dict[str, Any], manager: ChatContextManager) -> None:
        if not payload:
            return
        if payload.get("medical_conditions"):
            manager.set_medical_conditions(payload.get("medical_conditions"))
        if payload.get("allergies"):
            manager.set_allergies(payload.get("allergies"))
        if payload.get("dislikes"):
            manager.set_dislikes(payload.get("dislikes"))


class ChatOrchestrator:
    def __init__(self, app, logger) -> None:
        self.app = app
        self.logger = logger
        self.settings = self._load_settings(app)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.kb = KnowledgeStore(base_dir, self.settings, logger)
        self.tools = ToolCatalog(self.kb, format_explanation_block)
        self.client = self._build_client()

    @property
    def enabled(self) -> bool:
        return self.client is not None and bool(self.settings.api_key)

    def _load_settings(self, app) -> LLMSettings:
        cfg = app.config
        return LLMSettings(
            provider=cfg.get("LLM_PROVIDER", "disabled"),
            model=cfg.get("LLM_MODEL", "gpt-4o-mini"),
            api_key=cfg.get("LLM_API_KEY", ""),
            base_url=cfg.get("LLM_BASE_URL", ""),
            temperature=float(cfg.get("LLM_TEMPERATURE", 0.2)),
            max_tokens=int(cfg.get("LLM_MAX_TOKENS", 900)),
            embeddings_model=cfg.get("EMBEDDINGS_MODEL", "text-embedding-3-small"),
            rag_max_results=int(cfg.get("RAG_MAX_RESULTS", 4)),
            rag_index_path=cfg.get("RAG_INDEX_PATH")
            or os.path.join(os.path.dirname(__file__), "kb_index"),
        )

    def _build_client(self):
        if not self.settings.api_key or OpenAI is None:
            return None
        provider = (self.settings.provider or "openai").lower()
        if provider == "azure" and AzureOpenAI:
            return AzureOpenAI(
                api_key=self.settings.api_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=self.settings.base_url or os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                timeout=20,
            )
        return OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url or None, timeout=20)

    def _context_snapshot(self, manager: ChatContextManager) -> Dict[str, Any]:
        ctx = manager.context
        return {
            "allergies": ctx.allergies,
            "dislikes": ctx.dislikes,
            "medical_conditions": ctx.medical_conditions,
            "last_routine": ctx.last_routine,
            "last_diet": ctx.last_diet,
            "recent_history": (ctx.history or [])[-5:],
        }

    def _system_prompt(self) -> str:
        return (
            "Eres el orquestador conversacional de Fitter. Usa espanol conciso. "
            "Cuando el usuario solicite planes o aclaraciones, selecciona herramientas apropiadas y devuelve siempre un bloque de explicacion con titulos Datos usados / Criterios / Reglas / Fuentes. "
            "Incluye fuentes citables cuando uses search_kb. Prioriza seguridad y derivar a profesional si hay banderas rojas."
        )

    def respond(
        self,
        *,
        message: str,
        manager: ChatContextManager,
        parsed_intent: Optional[str],
        parsed_entities: Optional[Sequence[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        if not self.enabled:
            raise ChatServiceError("LLM orchestrator no configurado.")

        # Pre-screen
        screening = self.tools.dispatch("screen_user", {"medical_conditions": manager.context.medical_conditions}, manager)
        if screening["result"].get("needs_clearance"):
            return screening.get("responses") or []

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._system_prompt()},
            {
                "role": "system",
                "content": json.dumps({"context": self._context_snapshot(manager)}),
            },
            {"role": "user", "content": message},
        ]
        if parsed_intent:
            messages.append({"role": "system", "content": f"Intento NLU: {parsed_intent}"})

        first = self.client.chat.completions.create(
            model=self.settings.model,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            messages=messages,
            tools=self.tools.schemas(),
        )
        choice = first.choices[0].message
        responses: List[Dict[str, Any]] = []
        tool_messages: List[Dict[str, Any]] = []

        if choice.tool_calls:
            messages.append({"role": "assistant", "content": choice.content or "", "tool_calls": choice.tool_calls})
            for tc in choice.tool_calls:
                args = {}
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                tool_result = self.tools.dispatch(tc.function.name, args, manager)
                if tool_result.get("responses"):
                    responses.extend(tool_result["responses"])
                tool_messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(tool_result.get("result", {}))}
                )
            messages.extend(tool_messages)
            follow_up = self.client.chat.completions.create(
                model=self.settings.model,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
                messages=messages,
            )
            final_msg = follow_up.choices[0].message
        else:
            final_msg = choice

        if final_msg.content:
            final_custom = {
                "type": "assistant_message",
                "explanation": format_explanation_block(
                    {
                        "datos_usados": {"context": self._context_snapshot(manager)},
                        "criterios": ["Respuesta directa del modelo."],
                        "reglas": ["No inventar datos, adjuntar fuentes cuando existan."],
                        "fuentes": [],
                    }
                ),
            }
            responses.append({"text": final_msg.content, "custom": final_custom})

        # Ensure validation on generated plans
        validated: List[Dict[str, Any]] = []
        for item in responses:
            custom = item.get("custom") if isinstance(item, dict) else None
            if custom and isinstance(custom, dict) and custom.get("type") in {"routine_detail", "diet_plan"}:
                result = self.tools.dispatch("validate_plan", {"plan": custom}, manager)
                warnings = result.get("warnings") or []
                if warnings:
                    custom["validation_warnings"] = warnings
            validated.append(item)
        return validated
