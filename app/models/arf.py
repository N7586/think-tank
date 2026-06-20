from datetime import datetime
from app.extensions import db


class ARFAsset(db.Model):
    __tablename__ = 'arf_assets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_units = db.Column(db.Integer, nullable=False)
    units_sold = db.Column(db.Integer, default=0, nullable=False)
    expected_return = db.Column(db.Numeric(5, 2), nullable=False)
    risk_level = db.Column(db.String(10), nullable=False, default='medium')  # low, medium, high
    status = db.Column(db.String(10), nullable=False, default='active')  # active, closed, pending
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship('User', backref=db.backref('created_arfs', lazy=True, cascade='all, delete-orphan'))
    subscriptions = db.relationship('Subscription', backref='arf', lazy=True)

    @property
    def units_available(self):
        return self.total_units - self.units_sold

    @property
    def sold_percentage(self):
        if self.total_units == 0:
            return 0
        return round((self.units_sold / self.total_units) * 100, 1)

    @property
    def risk_label(self):
        return {'low': 'Faible', 'medium': 'Moyen', 'high': 'Élevé'}.get(self.risk_level, 'Inconnu')

    @property
    def risk_color(self):
        return {'low': 'success', 'medium': 'warning', 'high': 'danger'}.get(self.risk_level, 'secondary')

    def __repr__(self):
        return f'<ARF {self.name}>'


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    arf_id = db.Column(db.Integer, db.ForeignKey('arf_assets.id'), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # orange_money, mtn_momo
    phone_number = db.Column(db.String(20), nullable=False)
    transaction_ref = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(10), nullable=False, default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True, cascade='all, delete-orphan'))

    @property
    def status_label(self):
        return {'pending': 'En attente', 'completed': 'Complétée', 'failed': 'Échouée'}.get(self.status, 'Inconnu')

    @property
    def status_color(self):
        return {'pending': 'warning', 'completed': 'success', 'failed': 'danger'}.get(self.status, 'secondary')

    @property
    def payment_method_label(self):
        return {'orange_money': 'Orange Money', 'mtn_momo': 'MTN MoMo'}.get(self.payment_method, 'Inconnu')

    def __repr__(self):
        return f'<Subscription {self.id} - ARF {self.arf_id}>'
