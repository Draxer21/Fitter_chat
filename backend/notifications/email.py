# backend/notifications/email.py
"""
Utilidades para enviar correos electrónicos usando SMTP clásico.

Las credenciales se obtienen de variables de entorno:
 - SMTP_HOST (obligatoria)
 - SMTP_PORT (opcional, por defecto 587)
 - SMTP_USERNAME / SMTP_PASSWORD (opcional según servidor)
 - SMTP_USE_TLS (1 por defecto) / SMTP_USE_SSL (0 por defecto)
 - SMTP_DEFAULT_FROM (correo del remitente)
 - SMTP_DEFAULT_NAME (nombre descriptivo del remitente)
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional

from flask import current_app


def _bool_env(name: str, default: str = "0") -> bool:
    raw = os.getenv(name, default)
    if raw is None:
        return False
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _build_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str],
    from_name: Optional[str],
) -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = to_email
    sender = from_email or "no-reply@localhost"
    if from_name:
        msg["From"] = f"{from_name} <{sender}>"
    else:
        msg["From"] = sender
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
) -> None:
    """
    Envía un correo simple en texto plano.

    Lanza ValueError si hay configuración incompleta.
    """
    host = os.getenv("SMTP_HOST")
    if not host:
        raise ValueError("SMTP_HOST no está configurado.")

    port_raw = os.getenv("SMTP_PORT", "587")
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError(f"SMTP_PORT inválido: {port_raw}") from exc

    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_tls = _bool_env("SMTP_USE_TLS", "1")
    use_ssl = _bool_env("SMTP_USE_SSL", "0")

    if use_tls and use_ssl:
        raise ValueError("Configura solo uno de SMTP_USE_TLS o SMTP_USE_SSL.")

    sender_email = from_email or os.getenv("SMTP_DEFAULT_FROM")
    sender_name = from_name or os.getenv("SMTP_DEFAULT_NAME")

    if not sender_email:
        raise ValueError("Debe configurarse SMTP_DEFAULT_FROM o pasar from_email.")

    msg = _build_email(
        to_email=to_email,
        subject=subject,
        body=body,
        from_email=sender_email,
        from_name=sender_name,
    )

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port, timeout=10) as smtp:
        if use_tls and not use_ssl:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)

    try:
        current_app.logger.info("Correo enviado a %s con asunto '%s'", to_email, subject)
    except Exception:
        # Si no hay contexto de app, evitamos romper la ejecución.
        pass

