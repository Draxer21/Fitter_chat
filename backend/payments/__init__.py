"""
Módulo de pagos con MercadoPago
"""
from .models import Payment  # noqa: F401

try:
    from .routes import payments_bp
    __all__ = ['payments_bp', 'Payment']
except ImportError:
    __all__ = ['Payment']
