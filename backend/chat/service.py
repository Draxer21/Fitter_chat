import json
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple

import requests
from flask import Flask
from .models import ChatUserContext
from .context_manager import ChatContextManager
from .errors import ChatServiceError
from .orchestrator import ChatOrchestrator, format_explanation_block
from ..security.session import context_api_key_valid, session_uid


@dataclass
class ServiceResponse:
    payload: Any
    status_code: int = 200


class ChatService:
    """Orquesta validaciones, persistencia y llamadas a Rasa para /chat."""

    def __init__(self, app: Flask, db, http_session: requests.Session) -> None:
        self.app = app
        self.db = db
        self.http = http_session
        self._inflight_requests: Dict[str, object] = {}
        self._inflight_lock = Lock()
        self.orchestrator = ChatOrchestrator(app, app.logger)

    # -------- utilidades internas --------
    def rasa_url(self, path: str) -> str:
        path = path if path.startswith("/") else "/" + path
        return f"{self.app.config['RASA_BASE_URL']}{path}"

    def _ensure_dict(self, data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ChatServiceError("JSON invalido", 400)
        return data

    def _ensure_context_access(
        self,
        ctx: Optional[ChatUserContext],
        headers: Mapping[str, str],
        flask_session: MutableMapping[str, Any],
    ) -> None:
        expected_key = self.app.config.get("CHAT_CONTEXT_API_KEY", "")
        if context_api_key_valid(headers, expected_key):
            return
        uid = session_uid(flask_session)
        if uid is None:
            raise ChatServiceError("No autorizado para este contexto.", 401)
        if ctx is None:
            return
        if ctx.user_id and ctx.user_id != uid:
            raise ChatServiceError("No autorizado para este contexto.", 401)
        if not ctx.user_id:
            ctx.user_id = uid

    def _max_message_len(self) -> int:
        return int(self.app.config.get("MAX_MESSAGE_LEN", 5000))

    # -------- API publica --------
    def send_message(
        self,
        raw_data: Any,
        headers: Mapping[str, str],
        flask_session: MutableMapping[str, Any],
    ) -> ServiceResponse:
        data = self._ensure_dict(raw_data)
        sender = str(data.get("sender", "web-user")).strip() or "web-user"
        sender = sender[:80]
        message = str(data.get("message", "")).strip()
        if not message:
            raise ChatServiceError("El campo 'message' es obligatorio.", 400)
        if len(message) > self._max_message_len():
            raise ChatServiceError("El mensaje es demasiado largo.", 413)

        inflight_token = self._acquire_sender_slot(sender)
        if inflight_token is None:
            # A previous request is still running for this sender; avoid piling up and tripping locks
            return ServiceResponse(
                [{"text": "Sigo trabajando en tu solicitud anterior, dame unos segundos y vuelve a intentarlo."}],
                200,
            )

        ctx = ChatUserContext.get_or_create(sender, session_uid(flask_session))
        manager = ChatContextManager(ctx)
        rasa_payload: Dict[str, Any] = {"sender": sender, "message": message}
        metadata = manager.to_metadata()
        if metadata:
            rasa_payload["metadata"] = {"persisted_context": metadata}

        # Attempt to parse the user's message to capture intent/entities for history
        parsed_intent = None
        parsed_entities = None
        try:
            parse_resp = self.http.post(
                self.rasa_url(self.app.config["RASA_PARSE_ENDPOINT"]),
                json={"text": message},
                timeout=self.app.config.get("RASA_TIMEOUT_PARSE", 3),
            )
            parse_resp.raise_for_status()
            parse_payload = parse_resp.json()
            if isinstance(parse_payload, dict):
                parsed_intent = (parse_payload.get("intent") or {}).get("name")
                parsed_entities = [
                    {"entity": e.get("entity"), "value": e.get("value")} for e in (parse_payload.get("entities") or [])
                ]
        except Exception:
            # parsing is best-effort; continue without failing the request
            parsed_intent = None
            parsed_entities = None

        # record the user's message into history including parsed NLU metadata
        try:
            entry = {"type": "user_message", "text": message}
            if parsed_intent:
                entry["intent"] = parsed_intent
            if parsed_entities:
                entry["entities"] = parsed_entities
            manager.add_history_entry(entry)
        except Exception:
            # do not fail the request if history append fails
            pass

        try:
            self._ensure_context_access(ctx, headers, flask_session)

            payload = None
            if self.orchestrator and self.orchestrator.enabled:
                try:
                    payload = self.orchestrator.respond(
                        message=message,
                        manager=manager,
                        parsed_intent=parsed_intent,
                        parsed_entities=parsed_entities,
                    )
                except ChatServiceError:
                    raise
                except Exception:
                    self.app.logger.exception("LLM orchestrator fallo; se usa Rasa como respaldo")

            if payload is None:
                payload = self._call_rasa(rasa_payload)

            processed_payload, updated_context = self._process_bot_payload(payload, manager)

            if not updated_context:
                manager.touch()

            self.db.session.commit()
            return ServiceResponse(processed_payload, 200)
        except ChatServiceError:
            self.db.session.rollback()
            raise
        except requests.exceptions.RequestException as exc:
            self.db.session.rollback()
            self.app.logger.exception("Fallo al contactar Rasa en /chat/send")
            raise ChatServiceError(f"No se pudo contactar a Rasa: {exc}", 502)
        except json.JSONDecodeError:
            self.db.session.rollback()
            raise ChatServiceError("Respuesta de Rasa no es JSON valido.", 502)
        except Exception as exc:
            self.db.session.rollback()
            self.app.logger.exception("Error inesperado en /chat/send")
            raise ChatServiceError("No se pudo completar la solicitud.", 500) from exc
        finally:
            self._release_sender_slot(sender, inflight_token)

    def get_context(
        self,
        raw_sender: str,
        chat_id: Optional[str],
        headers: Mapping[str, str],
        flask_session: MutableMapping[str, Any],
    ) -> ServiceResponse:
        sender = (raw_sender or "").strip()[:80]
        if chat_id:
            chat_id = str(chat_id)[:80]
            ctx = ChatUserContext.query.filter_by(sender_id=sender, chat_id=chat_id).one_or_none()
        else:
            ctx = ChatUserContext.query.filter_by(sender_id=sender).one_or_none()
        if not ctx:
            expected_key = self.app.config.get("CHAT_CONTEXT_API_KEY", "")
            if context_api_key_valid(headers, expected_key) or session_uid(flask_session) is not None:
                return ServiceResponse({"found": False}, 404)
            raise ChatServiceError("Contexto no encontrado.", 404)
        try:
            self._ensure_context_access(ctx, headers, flask_session)
        except ChatServiceError:
            self.db.session.rollback()
            raise
        manager = ChatContextManager(ctx)
        self.db.session.commit()
        return ServiceResponse({"context": manager.to_dict()}, 200)

    def get_sessions(
        self,
        raw_sender: str,
        limit: int = 50,
        headers: Optional[Mapping[str, str]] = None,
        flask_session: Optional[MutableMapping[str, Any]] = None,
    ) -> ServiceResponse:
        """List chat sessions for a given sender.

        Returns a JSON payload with `sessions`: a list of session metadata objects
        containing `chat_id`, `created_at`, `last_interaction_at`, and simple flags
        for whether a last_diet/last_routine exists.
        """
        sender = (raw_sender or "").strip()[:80]
        headers = headers or {}
        # Require either API key or an active session to list sessions
        expected_key = self.app.config.get("CHAT_CONTEXT_API_KEY", "")
        if not (context_api_key_valid(headers, expected_key) or session_uid(flask_session) is not None):
            raise ChatServiceError("No autorizado para listar sesiones.", 401)

        query = ChatUserContext.query.filter_by(sender_id=sender).order_by(ChatUserContext.created_at.desc())
        if limit and isinstance(limit, int) and limit > 0:
            query = query.limit(limit)
        ctxs = query.all()

        sessions = []
        for c in ctxs:
            sessions.append(
                {
                    "chat_id": c.chat_id,
                    "created_at": (c.created_at.isoformat() if c.created_at else None),
                    "last_interaction_at": (c.last_interaction_at.isoformat() if c.last_interaction_at else None),
                    "has_last_diet": bool(c.last_diet),
                    "has_last_routine": bool(c.last_routine),
                }
            )

        return ServiceResponse({"sessions": sessions}, 200)

    # -------- concurrency helpers --------
    def _acquire_sender_slot(self, sender: str) -> Optional[object]:
        token = object()
        with self._inflight_lock:
            if sender in self._inflight_requests:
                return None
            self._inflight_requests[sender] = token
            return token

    def _release_sender_slot(self, sender: str, token: Optional[object]) -> None:
        if token is None:
            return
        with self._inflight_lock:
            current = self._inflight_requests.get(sender)
            if current is token:
                self._inflight_requests.pop(sender, None)

    def update_context(
        self,
        raw_sender: str,
        chat_id: Optional[str],
        raw_data: Any,
        headers: Mapping[str, str],
        flask_session: MutableMapping[str, Any],
    ) -> ServiceResponse:
        data = self._ensure_dict(raw_data)
        sender = (raw_sender or "").strip()[:80]
        # Merge chat_id into sender if provided so model.get_or_create can parse it,
        # or pass chat_id directly by constructing a combined sender string.
        sender_for_lookup = sender if not chat_id else f"{sender}::{chat_id}"
        ctx = ChatUserContext.get_or_create(sender_for_lookup, session_uid(flask_session))
        manager = ChatContextManager(ctx)
        try:
            self._ensure_context_access(ctx, headers, flask_session)

            updated = False
            if "allergies" in data:
                manager.set_allergies(data.get("allergies"))
                updated = True
            if "dislikes" in data:
                manager.set_dislikes(data.get("dislikes"))
                updated = True
            if "medical_conditions" in data:
                manager.set_medical_conditions(data.get("medical_conditions"))
                updated = True
            if "notes" in data:
                manager.set_notes(data.get("notes"))
                updated = True
            if isinstance(data.get("last_routine"), dict):
                manager.set_last_routine(data["last_routine"])
                updated = True
            if isinstance(data.get("last_diet"), dict):
                manager.set_last_diet(data["last_diet"])
                updated = True
            history_entry = data.get("history_entry")
            if isinstance(history_entry, dict):
                manager.add_history_entry(history_entry)
                updated = True

            if not updated:
                manager.touch()

            self.db.session.commit()
            return ServiceResponse({"ok": True, "context": manager.to_dict()}, 200)
        except ChatServiceError:
            self.db.session.rollback()
            raise

    # -------- internal helpers --------
    def _call_rasa(self, rasa_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        resp = self.http.post(
            self.rasa_url(self.app.config["RASA_REST_WEBHOOK"]),
            json=rasa_payload,
            timeout=self.app.config["RASA_TIMEOUT_SEND"],
        )
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, (list, tuple)):
            payload = [payload]
        return list(payload)

    def _process_bot_payload(self, payload: Any, manager: ChatContextManager) -> Tuple[List[Dict[str, Any]], bool]:
        items: List[Dict[str, Any]] = []
        updated_context = False
        if isinstance(payload, (list, tuple)):
            items = [p for p in payload if isinstance(p, dict)]
        elif isinstance(payload, dict):
            items = [payload]

        for item in items:
            bot_text = item.get("text") if isinstance(item, dict) else None
            if isinstance(bot_text, str) and bot_text.strip():
                try:
                    manager.add_history_entry({"type": "bot_message", "text": bot_text.strip()})
                except Exception:
                    pass

            custom_payload = None
            if isinstance(item, dict):
                custom_payload = item.get("custom")
                if not custom_payload and isinstance(item.get("json_message"), dict):
                    custom_payload = item.get("json_message")
            if not isinstance(custom_payload, dict):
                continue

            try:
                manager.add_history_entry({"type": "bot_custom", "data": custom_payload})
            except Exception:
                pass

            self._apply_context_updates(custom_payload.get("context_payload"), manager)

            msg_type = str(custom_payload.get("type") or "").strip().lower()
            if msg_type == "routine_detail":
                manager.set_last_routine(custom_payload)
                updated_context = True
            elif msg_type == "diet_plan":
                manager.set_last_diet(custom_payload)
                updated_context = True

            explanation = self._normalize_explanation(
                custom_payload.get("explanation")
                or custom_payload.get("explanation_text")
                or custom_payload.get("reason")
                or custom_payload.get("why")
            )
            source = custom_payload.get("source") if isinstance(custom_payload.get("source"), str) else None
            if explanation:
                history_entry: Dict[str, Any] = {
                    "type": f"{msg_type}_explanation" if msg_type else "explanation",
                    "explanation": explanation,
                }
                if source:
                    history_entry["source"] = source
                try:
                    manager.add_history_entry(history_entry)
                except Exception:
                    pass

        fallback_items: List[Dict[str, Any]] = []
        if not items:
            if isinstance(payload, list):
                fallback_items = [p for p in payload if isinstance(p, dict)]
            elif isinstance(payload, dict):
                fallback_items = [payload]
        return items or fallback_items, updated_context

    def _normalize_explanation(self, raw: Any) -> Optional[str]:
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        if isinstance(raw, dict):
            try:
                return format_explanation_block(raw)
            except Exception:
                return None
        return None

    def _apply_context_updates(self, payload: Any, manager: ChatContextManager) -> None:
        if not isinstance(payload, dict):
            return
        if payload.get("allergies"):
            manager.set_allergies(payload.get("allergies"))
        if payload.get("dislikes"):
            manager.set_dislikes(payload.get("dislikes"))
        if payload.get("medical_conditions"):
            manager.set_medical_conditions(payload.get("medical_conditions"))
