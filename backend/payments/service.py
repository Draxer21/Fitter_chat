"""
Servicio de integración con MercadoPago
"""
import mercadopago
from flask import current_app
from backend.extensions import db
from backend.payments.models import Payment
from backend.orders.models import Order


class MercadoPagoService:
    """Servicio para manejar operaciones con MercadoPago"""

    def __init__(self):
        """Inicializar el SDK de MercadoPago"""
        access_token = current_app.config.get('MERCADOPAGO_ACCESS_TOKEN')
        if not access_token:
            raise ValueError("MERCADOPAGO_ACCESS_TOKEN no está configurado")

        self.sdk = mercadopago.SDK(access_token)

    def create_preference(self, order_id, items, payer_info=None, back_urls=None):
        """
        Crear una preferencia de pago en MercadoPago

        Args:
            order_id: ID de la orden
            items: Lista de items del carrito
            payer_info: Información del pagador (opcional)
            back_urls: URLs de retorno (opcional)

        Returns:
            dict: Respuesta de MercadoPago con la preferencia creada
        """
        # Obtener la orden
        order = Order.query.get(order_id)
        if not order:
            raise ValueError(f"Orden {order_id} no encontrada")

        # Preparar items para MercadoPago
        mp_items = []
        for item in items:
            mp_items.append({
                "title": item.get('name', 'Producto'),
                "quantity": item.get('quantity', 1),
                "unit_price": float(item.get('price', 0)),
                "currency_id": "CLP"
            })

        # Configurar preferencia
        preference_data = {
            "items": mp_items,
            "external_reference": str(order_id),
            "statement_descriptor": "FITTER",
            "payment_methods": {
                "installments": 12,  # Hasta 12 cuotas
            },
        }

        # Solo agregar notification_url si es una URL de producción válida (no localhost, no ngrok)
        notification_url = (current_app.config.get('MERCADOPAGO_NOTIFICATION_URL') or "").strip()
        _invalid_hosts = ("localhost", "127.0.0.1", "ngrok", "ngrok-free.app", "0.0.0.0")
        if notification_url and not any(h in notification_url for h in _invalid_hosts):
            preference_data["notification_url"] = notification_url

        # Agregar información del pagador si está disponible
        if payer_info:
            payer_email = payer_info.get('email', '')
            access_token = current_app.config.get('MERCADOPAGO_ACCESS_TOKEN', '')
            is_test_mode = access_token.startswith('TEST-')
            if is_test_mode:
                test_buyer_email = current_app.config.get('MP_TEST_BUYER_EMAIL', '').strip()
                if test_buyer_email:
                    payer_email = test_buyer_email
            preference_data["payer"] = {
                "name": payer_info.get('name') or 'Test',
                "surname": payer_info.get('surname') or 'User',
                "email": payer_email,
            }

        # URLs de retorno - SIEMPRE configurarlas
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5000')
        base_url = base_url.rstrip('/')

        preference_data["back_urls"] = {
            "success": f"{base_url}/carrito/payment/success",
            "failure": f"{base_url}/carrito/payment/failure",
            "pending": f"{base_url}/carrito/payment/pending"
        }

        # NO usar auto_return por ahora para evitar problemas
        # preference_data["auto_return"] = "approved"

        current_app.logger.info(f"URLs de retorno: {preference_data['back_urls']}")

        # Crear preferencia en MercadoPago
        preference_response = self.sdk.preference().create(preference_data)

        if preference_response["status"] == 201:
            # Guardar información del pago
            payment = Payment(
                order_id=order_id,
                preference_id=preference_response["response"]["id"],
                transaction_amount=float(order.total_amount),
                currency_id="CLP",
                status="pending",
                external_reference=str(order_id),
                payer_email=payer_info.get('email') if payer_info else None
            )
            db.session.add(payment)
            db.session.commit()

            return {
                "success": True,
                "preference_id": preference_response["response"]["id"],
                "init_point": preference_response["response"]["init_point"],  # Para desktop
                "sandbox_init_point": preference_response["response"]["sandbox_init_point"],  # Para testing
                "payment_id": payment.id
            }
        else:
            raise Exception(f"Error al crear preferencia: {preference_response}")

    def create_payment(self, token, transaction_amount, installments,
                       payment_method_id, issuer_id, payer_email,
                       payer_identification, order_id):
        """
        Crear un pago directo con Checkout API (sin redirección).
        """
        access_token = current_app.config.get('MERCADOPAGO_ACCESS_TOKEN', '')
        is_test_mode = access_token.startswith('TEST-')
        if is_test_mode:
            # En sandbox, MP recomienda usar un test-user comprador real.
            # Si MP_TEST_BUYER_EMAIL está configurado, lo usamos; si no,
            # usamos el email del pagador (el pago puede ser rechazado por MP
            # pero no rompe el backend).
            test_buyer_email = current_app.config.get('MP_TEST_BUYER_EMAIL', '').strip()
            if test_buyer_email:
                effective_email = test_buyer_email
            else:
                current_app.logger.warning(
                    "MP_TEST_BUYER_EMAIL no configurado. En modo sandbox MP puede rechazar "
                    "el pago si el email '%s' no es un test-user. "
                    "Crea un usuario de prueba en mercadopago.com/developers y configura "
                    "MP_TEST_BUYER_EMAIL para evitar rechazos.",
                    payer_email,
                )
                effective_email = payer_email
        else:
            effective_email = payer_email

        # CLP no tiene decimales — MP rechaza si se envían centavos
        amount = int(transaction_amount) if is_test_mode else float(transaction_amount)

        payment_data = {
            "transaction_amount": amount,
            "token": token,
            "description": "Fitter",
            "installments": int(installments),
            "payment_method_id": payment_method_id,
            "payer": {
                "email": effective_email,
                "identification": payer_identification or {},
            },
            "external_reference": str(order_id),
            "statement_descriptor": "FITTER",
        }

        if issuer_id:
            payment_data["issuer_id"] = issuer_id

        notification_url = (current_app.config.get('MERCADOPAGO_NOTIFICATION_URL') or "").strip()
        _invalid_hosts = ("localhost", "127.0.0.1", "ngrok", "ngrok-free.app", "0.0.0.0")
        if notification_url and not any(h in notification_url for h in _invalid_hosts):
            payment_data["notification_url"] = notification_url

        return self.sdk.payment().create(payment_data)

    def get_payment_info(self, payment_id):
        """
        Obtener información de un pago desde MercadoPago

        Args:
            payment_id: ID del pago en MercadoPago

        Returns:
            dict: Información del pago
        """
        payment_response = self.sdk.payment().get(payment_id)

        if payment_response["status"] == 200:
            return payment_response["response"]
        else:
            raise Exception(f"Error al obtener información del pago: {payment_response}")

    def process_webhook_notification(self, data):
        """
        Procesar notificación de webhook de MercadoPago

        Args:
            data: Datos de la notificación

        Returns:
            bool: True si se procesó correctamente
        """
        try:
            # Obtener tipo de notificación
            notification_type = data.get('type')

            if notification_type == 'payment':
                payment_id = data.get('data', {}).get('id')

                if payment_id:
                    # Obtener información del pago
                    payment_info = self.get_payment_info(payment_id)

                    # Buscar el pago en la base de datos por external_reference
                    external_reference = payment_info.get('external_reference')
                    if external_reference:
                        order_id = int(external_reference)
                        payment = Payment.query.filter_by(order_id=order_id).first()

                        if payment:
                            # Actualizar información del pago
                            payment.payment_id = str(payment_id)
                            payment.status = payment_info.get('status')
                            payment.payment_method_id = payment_info.get('payment_method_id')
                            payment.payment_type_id = payment_info.get('payment_type_id')
                            payment.merchant_order_id = str(payment_info.get('order', {}).get('id', ''))

                            if payment.status == 'approved':
                                from datetime import datetime
                                payment.approved_at = datetime.utcnow()

                                # Actualizar estado de la orden
                                order = Order.query.get(order_id)
                                if order:
                                    order.payment_status = 'paid'
                                    order.status = 'confirmed'
                                    # Auto-activar suscripción si corresponde
                                    try:
                                        from backend.payments.routes import _maybe_activate_subscription
                                        from backend.login.models import User
                                        user = User.query.get(order.user_id) if order.user_id else None
                                        if user:
                                            _maybe_activate_subscription(order, user)
                                    except Exception as sub_exc:
                                        current_app.logger.warning("No se pudo activar suscripción desde webhook: %s", sub_exc)

                            elif payment.status in ['rejected', 'cancelled']:
                                # Actualizar estado de la orden
                                order = Order.query.get(order_id)
                                if order:
                                    order.payment_status = 'failed'

                            db.session.commit()
                            return True

            return False

        except Exception as e:
            current_app.logger.error(f"Error procesando webhook: {str(e)}")
            db.session.rollback()
            return False
