"""
Rutas para el módulo de pagos con MercadoPago
"""
from typing import Optional
from flask import Blueprint, request, jsonify, current_app, session
from backend.extensions import db
from backend.payments.service import MercadoPagoService
from backend.payments.models import Payment
from backend.orders.models import Order, OrderItem
from backend.login.models import User

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


@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook para recibir notificaciones de MercadoPago
    """
    try:
        data = request.get_json()
        
        # Procesar notificación
        mp_service = MercadoPagoService()
        success = mp_service.process_webhook_notification(data)
        
        if success:
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'status': 'ignored'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Error en webhook: {str(e)}")
        return jsonify({'error': 'Error procesando webhook'}), 500


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
