"""
Modelos para el sistema de pagos
"""
from backend.extensions import db
from datetime import datetime


class Payment(db.Model):
    """Modelo para registrar pagos"""
    __tablename__ = 'payment'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    
    # Información de MercadoPago
    preference_id = db.Column(db.String(255), unique=True, nullable=False)
    payment_id = db.Column(db.String(255), unique=True, nullable=True)
    
    # Estado del pago
    status = db.Column(db.String(50), nullable=False, default='pending')
    # pending, approved, rejected, cancelled, refunded, in_process
    
    # Montos
    transaction_amount = db.Column(db.Float, nullable=False)
    currency_id = db.Column(db.String(10), default='CLP')
    
    # Método de pago usado
    payment_method_id = db.Column(db.String(50), nullable=True)
    payment_type_id = db.Column(db.String(50), nullable=True)
    
    # Metadatos adicionales
    merchant_order_id = db.Column(db.String(255), nullable=True)
    external_reference = db.Column(db.String(255), nullable=True)
    
    # Información del pagador (opcional)
    payer_email = db.Column(db.String(255), nullable=True)
    payer_id = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    order = db.relationship('Order', backref=db.backref('payment', uselist=False), lazy='select')
    
    def __repr__(self):
        return f'<Payment {self.id} - Order {self.order_id} - Status: {self.status}>'
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'preference_id': self.preference_id,
            'payment_id': self.payment_id,
            'status': self.status,
            'transaction_amount': self.transaction_amount,
            'currency_id': self.currency_id,
            'payment_method_id': self.payment_method_id,
            'payment_type_id': self.payment_type_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
        }
