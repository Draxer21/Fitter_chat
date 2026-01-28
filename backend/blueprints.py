"""Declarative registration of application blueprints."""

from dataclasses import dataclass
from importlib import import_module
from typing import Iterable, Optional

from flask import Blueprint, Flask


@dataclass(frozen=True)
class BlueprintSpec:
    label: str
    import_path: str
    attr: str = "bp"
    url_prefix: Optional[str] = None

    def load(self) -> Blueprint:
        module = import_module(self.import_path)
        return getattr(module, self.attr)


_BLUEPRINTS: Iterable[BlueprintSpec] = (
    BlueprintSpec(
        label="inventario",
        import_path="backend.gestor_inventario.routes",
        url_prefix="/inventario",
    ),
    BlueprintSpec(
        label="carrito",
        import_path="backend.carritoapp.routes",
        url_prefix="/carrito",
    ),
    BlueprintSpec(
        label="producto",
        import_path="backend.producto.routes",
        url_prefix="/producto",
    ),
    BlueprintSpec(
        label="auth",
        import_path="backend.login.routes",
        url_prefix="/auth",
    ),
    BlueprintSpec(
        label="notifications",
        import_path="backend.notifications.routes",
        url_prefix="/notifications",
    ),
    BlueprintSpec(
        label="orders",
        import_path="backend.orders.routes",
    ),
    BlueprintSpec(
        label="profile",
        import_path="backend.profile.routes",
        url_prefix="/profile",
    ),
    BlueprintSpec(
        label="payments",
        import_path="backend.payments.routes",
        attr="payments_bp",
    ),
    BlueprintSpec(
        label="metrics",
        import_path="backend.metrics.routes",
    ),
    BlueprintSpec(
        label="classes",
        import_path="backend.classes.routes",
        url_prefix="/classes",
    ),
    BlueprintSpec(
        label="plans",
        import_path="backend.plans.routes",
        url_prefix="/api",
        attr="plans_bp",
    ),
)


def register_blueprints(app: Flask) -> None:
    """Itera sobre el catálogo y registra cada blueprint."""
    for spec in _BLUEPRINTS:
        try:
            blueprint = spec.load()
            app.register_blueprint(blueprint, url_prefix=spec.url_prefix)
        except Exception as exc:  # pragma: no cover - defensivo
            app.logger.warning("No se pudo registrar blueprint %s: %s", spec.label, exc)
