"""Helpers para inicializar extensiones y cargar modelos."""

import importlib
import os
from typing import Iterable, Tuple

from flask import Flask

from .extensions import db, migrate


def init_extensions(app: Flask) -> None:
    """Inicializa db/migrate compartidos."""
    db.init_app(app)
    migrations_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "migrations")
    )
    migrate.init_app(app, db, directory=migrations_dir)


_MODEL_MODULES: Iterable[Tuple[str, str]] = (
    ("gestor_inventario", "backend.gestor_inventario.models"),
    ("classes", "backend.classes.models"),
    ("login", "backend.login.models"),
    ("profile", "backend.profile.models"),
    ("metrics", "backend.metrics"),
)


def load_models(app: Flask) -> None:
    """Importa defensivamente los modelos para que Alembic vea la metadata."""
    with app.app_context():
        for label, module_path in _MODEL_MODULES:
            try:
                importlib.import_module(module_path)
            except Exception as exc:  # pragma: no cover - vigilancia defensiva
                app.logger.warning(
                    "No se pudieron cargar modelos de %s: %s", label, exc
                )
