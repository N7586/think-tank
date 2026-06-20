from datetime import datetime
import uuid
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False, default='subscription')  # subscription, deposit, withdrawal
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(5), nullable=False, default='XOF')
    payment_method = db.Column(db.String(20), nullable=False)  # orange_money, mtn_momo
    phone_number = db.Column(db.String(20), nullable=False)
    reference = db.Column(db.String(100), nullable=False, unique=True)
    provider_ref = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(15), nullable=False, default='pending')  # pending, processing, completed, failed, cancelled
    failure_reason = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True, cascade='all, delete-orphan'))
    subscription = db.relationship('Subscription', backref=db.backref('transaction', lazy=True, cascade='all, delete-orphan'))

    @staticmethod
    def generate_reference():
        return f'TSI-{datetime.utcnow().strftime("%Y%m%d")}-{uuid.uuid4().hex[:8].upper()}'

    @property
    def status_label(self):
        return {
            'pending': 'En attente',
            'processing': 'En cours',
            'completed': 'Complétée',
            'failed': 'Échouée',
            'cancelled': 'Annulée'
        }.get(self.status, 'Inconnu')

    @property
    def status_color(self):
        return {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'failed': 'danger',
            'cancelled': 'secondary'
        }.get(self.status, 'secondary')

    @property
    def type_label(self):
        return {
            'subscription': 'Souscription ARF',
            'deposit': 'Dépôt',
            'withdrawal': 'Retrait'
        }.get(self.type, 'Autre')

    @property
    def payment_method_label(self):
        return {'orange_money': 'Orange Money', 'mtn_momo': 'MTN MoMo'}.get(self.payment_method, 'Inconnu')

    def __repr__(self):
        return f'<Transaction {self.reference}>'
