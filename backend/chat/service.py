import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional

import requests
from flask import Flask
from .models import ChatUserContext
from .context_manager import ChatContextManager
from ..security.session import context_api_key_valid, session_uid


class ChatServiceError(Exception):
    """Errores controlados que deben convertise en respuestas JSON."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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

        ctx = ChatUserContext.get_or_create(sender, session_uid(flask_session))
        manager = ChatContextManager(ctx)
        rasa_payload: Dict[str, Any] = {"sender": sender, "message": message}
        metadata = manager.to_metadata()
        if metadata:
            rasa_payload["metadata"] = {"persisted_context": metadata}

        try:
            self._ensure_context_access(ctx, headers, flask_session)
            resp = self.http.post(
                self.rasa_url(self.app.config["RASA_REST_WEBHOOK"]),
                json=rasa_payload,
                timeout=self.app.config["RASA_TIMEOUT_SEND"],
            )
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, (list, tuple)):
                payload = [payload]

            updated_context = False
            for item in payload:
                if not isinstance(item, dict):
                    continue
                custom_payload = item.get("custom")
                if not custom_payload and isinstance(item.get("json_message"), dict):
                    custom_payload = item["json_message"]
                if not isinstance(custom_payload, dict):
                    continue
                msg_type = str(custom_payload.get("type") or "").strip().lower()
                explanation = None
                for key in ("explanation", "reason", "why"):
                    raw_exp = custom_payload.get(key)
                    if isinstance(raw_exp, str) and raw_exp.strip():
                        explanation = raw_exp.strip()
                        break
                source = custom_payload.get("source") if isinstance(custom_payload.get("source"), str) else None

                if msg_type == "routine_detail":
                    manager.set_last_routine(custom_payload)
                    updated_context = True
                elif msg_type == "diet_plan":
                    manager.set_last_diet(custom_payload)
                    updated_context = True
                if explanation:
                    entry = {
                        "type": f"{msg_type}_explanation" if msg_type else "explanation",
                        "explanation": explanation,
                    }
                    if source:
                        entry["source"] = source
                    manager.add_history_entry(entry)

            if not updated_context:
                manager.touch()

            self.db.session.commit()
            return ServiceResponse(list(payload), 200)
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

    def get_context(
        self,
        raw_sender: str,
        headers: Mapping[str, str],
        flask_session: MutableMapping[str, Any],
    ) -> ServiceResponse:
        sender = (raw_sender or "").strip()[:80]
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

    def update_context(
        self,
        raw_sender: str,
        raw_data: Any,
        headers: Mapping[str, str],
        flask_session: MutableMapping[str, Any],
    ) -> ServiceResponse:
        data = self._ensure_dict(raw_data)
        sender = (raw_sender or "").strip()[:80]
        ctx = ChatUserContext.get_or_create(sender, session_uid(flask_session))
        manager = ChatContextManager(ctx)
        try:
            self._ensure_context_access(ctx, headers, flask_session)

            updated = False
            if "allergies" in data:
                manager.set_allergies(data.get("allergies"))
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
