"""
Rutas para el módulo de pagos con MercadoPago
"""
import hashlib
import hmac
from typing import Optional
from flask import Blueprint, request, jsonify, current_app, session
from backend.extensions import db
from backend.payments.service import MercadoPagoService
from backend.payments.models import Payment
from backend.orders.models import Order, OrderItem
from backend.login.models import User
from backend.subscriptions.models import Subscription
from backend.gestor_inventario.models import Producto

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


def _current_user() -> Optional[User]:
    """Obtener el usuario actual de la sesión"""
    uid = session.get("uid")
    if not uid:
        return None
    return db.session.get(User, uid)


def _require_auth():
    """Verificar que el usuario esté autenticado"""
    user = _current_user()
    if not user:
        return None, (jsonify({'error': 'No autorizado'}), 401)
    return user, None


@payments_bp.route('/create-preference', methods=['POST'])
def create_preference():
    """
    Crear una preferencia de pago en MercadoPago

    Request body:
    {
        "order_id": 123,
        "payer_info": {
            "name": "Juan",
            "surname": "Pérez",
            "email": "juan@example.com"
        }
    }
    """
    # Verificar autenticación
    current_user, error = _require_auth()
    if error:
        return error

    try:
        data = request.get_json()
        order_id = data.get('order_id')

        if not order_id:
            return jsonify({'error': 'order_id es requerido'}), 400

        # Verificar que la orden existe y pertenece al usuario
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Orden no encontrada'}), 404

        if order.user_id != current_user.id:
            return jsonify({'error': 'No autorizado'}), 403

        # Verificar que la orden no tenga ya un pago aprobado
        existing_payment = Payment.query.filter_by(
            order_id=order_id,
            status='approved'
        ).first()

        if existing_payment:
            return jsonify({'error': 'Esta orden ya tiene un pago aprobado'}), 400

        # Preparar items de la orden
        items = []
        for item in order.items:
            items.append({
                'name': item.product_name,
                'quantity': item.quantity,
                'price': item.price
            })

        # Información del pagador
        payer_info = data.get('payer_info', {})
        if not payer_info.get('email'):
            payer_info['email'] = current_user.email

        # Crear preferencia
        mp_service = MercadoPagoService()
        result = mp_service.create_preference(
            order_id=order_id,
            items=items,
            payer_info=payer_info
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creando preferencia: {str(e)}")
        return jsonify({'error': 'Error al crear preferencia de pago'}), 500


def _verify_mp_signature() -> bool:
    """
    Verifica la firma HMAC-SHA256 enviada por MercadoPago en el webhook.
    Documentación: https://www.mercadopago.com.ar/developers/es/docs/your-integrations/notifications/webhooks
    Si MERCADOPAGO_WEBHOOK_SECRET no está configurado, rechaza la solicitud.
    """
    secret = current_app.config.get("MERCADOPAGO_WEBHOOK_SECRET", "").strip()
    if not secret:
        current_app.logger.warning(
            "MERCADOPAGO_WEBHOOK_SECRET no configurado — webhook rechazado. "
            "Define la variable de entorno para habilitar notificaciones de pago."
        )
        return False

    # MercadoPago envía: x-signature: ts=<timestamp>,v1=<hmac>
    # y x-request-id en los headers
    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")

    ts = ""
    v1 = ""
    for part in x_signature.split(","):
        if part.startswith("ts="):
            ts = part[3:]
        elif part.startswith("v1="):
            v1 = part[3:]

    if not ts or not v1:
        return False

    # El data.id viene del query string o del body
    data_id = request.args.get("data.id", "")
    if not data_id:
        body = request.get_json(silent=True) or {}
        data_id = str((body.get("data") or {}).get("id", ""))

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook para recibir notificaciones de MercadoPago.
    Verifica la firma HMAC-SHA256 antes de procesar cualquier notificación.
    """
    if not _verify_mp_signature():
        current_app.logger.warning("Webhook rechazado: firma inválida o ausente")
        return jsonify({'error': 'Firma inválida'}), 401

    try:
        data = request.get_json()

        # Procesar notificación
        mp_service = MercadoPagoService()
        success = mp_service.process_webhook_notification(data)

        if success:
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'status': 'ignored'}), 200

    except Exception:
        current_app.logger.error("Error en webhook de MercadoPago")
        return jsonify({'error': 'Error procesando webhook'}), 500


@payments_bp.route('/public-key', methods=['GET'])
def get_public_key():
    """Devuelve la public key de MP y si estamos en modo sandbox (test)."""
    access_token = current_app.config.get('MERCADOPAGO_ACCESS_TOKEN', '')
    public_key = current_app.config.get('MERCADOPAGO_PUBLIC_KEY', '')
    is_test_mode = access_token.startswith('TEST-') or public_key.startswith('TEST-')
    return jsonify({
        'public_key': public_key,
        'is_test_mode': is_test_mode,
    })


# Palabras clave para identificar el tipo de plan en el nombre del producto
_PLAN_KEYWORDS = {
    "black":   ["black", "negro", "élite", "elite"],
    "premium": ["premium", "pro", "avanzado"],
    "basic":   ["basic", "básico", "basico", "básica", "basica", "starter", "inicial"],
}

_SUBSCRIPTION_CATEGORIES = {
    "suscripcion", "suscripción", "subscription",
    "plan", "membresia", "membresía",
    "membership",   # categoria usada en seed
}


def _detect_plan_type(product_name: str, categoria: str) -> Optional[str]:
    """Detecta el tipo de plan a partir del nombre y categoría del producto."""
    name_lower = (product_name or "").lower()
    for plan, keywords in _PLAN_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return plan
    return None


def _is_subscription_product(producto: Producto) -> bool:
    """Devuelve True si el producto es un plan de suscripción."""
    cat = (producto.categoria or "").lower().strip()
    if cat in _SUBSCRIPTION_CATEGORIES:
        return True
    # Fallback: detectar por nombre si contiene palabras de plan
    return _detect_plan_type(producto.nombre, cat) is not None


def _maybe_activate_subscription(order: Order, user: User) -> None:
    """Si la orden incluye productos de suscripción, activa el plan correspondiente."""
    from datetime import timedelta
    if not user:
        return
    for item in order.items:
        if not item.product_id:
            continue
        producto = db.session.get(Producto, item.product_id)
        if not producto or not _is_subscription_product(producto):
            continue
        plan_type = _detect_plan_type(producto.nombre, producto.categoria or "")
        if not plan_type:
            plan_type = "basic"
        # Cancelar suscripción activa previa (upgrade/cambio de plan)
        existing = Subscription.query.filter_by(user_id=user.id, status="active").first()
        if existing:
            existing.status = "upgraded"
            existing.cancelled_at = __import__("datetime").datetime.utcnow()
        # Crear nueva suscripción con vencimiento a 30 días
        from datetime import datetime as _dt2
        now = _dt2.utcnow()
        new_sub = Subscription(
            user_id=user.id,
            plan_type=plan_type,
            status="active",
            start_date=now,
            end_date=now + timedelta(days=30),
            auto_renew=True,
        )
        db.session.add(new_sub)
        current_app.logger.info(
            "Suscripción '%s' activada para usuario %s desde orden %s",
            plan_type, user.id, order.id,
        )
        break  # Solo un plan por orden


@payments_bp.route('/process-card', methods=['POST'])
def process_card():
    """
    Procesar pago con Checkout API (tarjeta tokenizada).
    Recibe el token generado por MP.js en el frontend.
    """
    current_user, error = _require_auth()
    if error:
        return error

    data = request.get_json(force=True, silent=True) or {}
    token = data.get('token')
    payment_method_id = data.get('payment_method_id')
    issuer_id = data.get('issuer_id')
    installments = data.get('installments', 1)
    transaction_amount = data.get('transaction_amount')
    order_id = data.get('order_id')
    payer = data.get('payer', {})

    if not all([token, payment_method_id, transaction_amount, order_id]):
        return jsonify({'error': 'Faltan campos requeridos: token, payment_method_id, transaction_amount, order_id'}), 400

    order = Order.query.get(order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'error': 'Orden no encontrada'}), 404

    try:
        mp_service = MercadoPagoService()
        response = mp_service.create_payment(
            token=token,
            transaction_amount=float(transaction_amount),
            installments=int(installments),
            payment_method_id=payment_method_id,
            issuer_id=issuer_id,
            payer_email=payer.get('email') or current_user.email,
            payer_identification=payer.get('identification', {}),
            order_id=order_id,
        )

        http_status = response.get('status')
        mp_body     = response.get('response', {})

        if http_status not in (200, 201):
            # MP returned an HTTP error (bad request, invalid users, etc.)
            mp_message = (
                mp_body.get('message')
                or mp_body.get('error')
                or f"HTTP {http_status}"
            )
            current_app.logger.error(
                "MP rechazó el pago (HTTP %s): %s | payload: %s",
                http_status, mp_body, payment_data,
            )

            # Detect sandbox / test-user issue specifically
            is_test = current_app.config.get('MERCADOPAGO_ACCESS_TOKEN', '').startswith('TEST-')
            invalid_users = 'invalid users' in mp_message.lower() or 'invalid_users' in mp_message.lower()
            if is_test and (invalid_users or http_status == 400):
                user_hint = (
                    "Estás en modo sandbox. El email del pagador debe ser un "
                    "test-user de MercadoPago. Crea uno en mercadopago.com/developers "
                    "y configura MP_TEST_BUYER_EMAIL en el servidor."
                )
                return jsonify({
                    'error': f'MercadoPago sandbox: {mp_message}',
                    'hint': user_hint,
                    'detail': mp_body,
                }), 400

            return jsonify({
                'error': f'MercadoPago rechazó el pago: {mp_message}',
                'detail': mp_body,
            }), 400

        mp_data = mp_body

        from datetime import datetime as _dt
        import uuid as _uuid
        payment = Payment(
            order_id=order_id,
            preference_id=f"direct-{order_id}-{_uuid.uuid4().hex[:8]}",
            payment_id=str(mp_data.get('id', '')),
            transaction_amount=float(transaction_amount),
            currency_id='CLP',
            status=mp_data.get('status', 'pending'),
            payment_method_id=mp_data.get('payment_method_id'),
            payment_type_id=mp_data.get('payment_type_id'),
            external_reference=str(order_id),
            payer_email=payer.get('email') or current_user.email,
        )
        db.session.add(payment)

        mp_status        = mp_data.get('status')
        mp_status_detail = mp_data.get('status_detail', '')

        if mp_status == 'approved':
            order.payment_status = 'paid'
            order.status = 'confirmed'
            payment.approved_at = _dt.utcnow()
            _maybe_activate_subscription(order, current_user)
        elif mp_status == 'rejected':
            order.payment_status = 'failed'
            current_app.logger.warning(
                "Pago rechazado por MP — order %s, status_detail: %s",
                order_id, mp_status_detail,
            )

        db.session.commit()

        # Translate common MP rejection codes into Spanish for the UI
        _STATUS_DETAIL_ES = {
            'cc_rejected_bad_filled_security_code': 'CVV incorrecto.',
            'cc_rejected_bad_filled_date':          'Fecha de vencimiento incorrecta.',
            'cc_rejected_bad_filled_card_number':   'Número de tarjeta incorrecto.',
            'cc_rejected_bad_filled_other':         'Datos de tarjeta incorrectos.',
            'cc_rejected_blacklist':                'Tarjeta rechazada por el banco.',
            'cc_rejected_call_for_authorize':       'Llama a tu banco para autorizar el pago.',
            'cc_rejected_card_disabled':            'Tarjeta desactivada. Contacta tu banco.',
            'cc_rejected_duplicated_payment':       'Pago duplicado detectado.',
            'cc_rejected_high_risk':                'Pago rechazado por riesgo. Usa otra tarjeta.',
            'cc_rejected_insufficient_amount':      'Saldo insuficiente.',
            'cc_rejected_invalid_installments':     'Cuotas no disponibles para esta tarjeta.',
            'cc_rejected_max_attempts':             'Demasiados intentos. Espera un momento.',
            'cc_rejected_other_reason':             'Tarjeta rechazada. Intenta con otra.',
        }
        detail_es = _STATUS_DETAIL_ES.get(mp_status_detail, mp_status_detail)

        return jsonify({
            'status':        mp_status,
            'status_detail': mp_status_detail,
            'status_detail_es': detail_es,
            'order_id':      order_id,
            'payment_id':    mp_data.get('id'),
        }), 200

    except Exception:
        current_app.logger.exception("Error en /api/payments/process-card")
        db.session.rollback()
        return jsonify({'error': 'Error interno al procesar el pago'}), 500


@payments_bp.route('/status/<int:payment_id>', methods=['GET'])
def get_payment_status(payment_id):
    """
    Obtener el estado de un pago
    """
    # Verificar autenticación
    current_user, error = _require_auth()
    if error:
        return error

    try:
        payment = Payment.query.get(payment_id)

        if not payment:
            return jsonify({'error': 'Pago no encontrado'}), 404

        # Verificar que el pago pertenece al usuario
        if payment.order.user_id != current_user.id:
            return jsonify({'error': 'No autorizado'}), 403

        return jsonify(payment.to_dict()), 200

    except Exception as e:
        current_app.logger.error(f"Error obteniendo estado del pago: {str(e)}")
        return jsonify({'error': 'Error al obtener estado del pago'}), 500


@payments_bp.route('/order/<int:order_id>', methods=['GET'])
def get_order_payment(order_id):
    """
    Obtener información del pago de una orden
    """
    # Verificar autenticación
    current_user, error = _require_auth()
    if error:
        return error

    try:
        order = Order.query.get(order_id)

        if not order:
            return jsonify({'error': 'Orden no encontrada'}), 404

        if order.user_id != current_user.id:
            return jsonify({'error': 'No autorizado'}), 403

        payment = Payment.query.filter_by(order_id=order_id).order_by(Payment.created_at.desc()).first()

        if not payment:
            return jsonify({'error': 'No se encontró información de pago para esta orden'}), 404

        return jsonify(payment.to_dict()), 200

    except Exception as e:
        current_app.logger.error(f"Error obteniendo pago de orden: {str(e)}")
        return jsonify({'error': 'Error al obtener información del pago'}), 500
