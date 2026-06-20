from datetime import datetime
from app.extensions import db


class MarketplaceOffer(db.Model):
    __tablename__ = 'marketplace_offers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    contract_type = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Numeric(15, 2), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(10), nullable=False, default='available')  # available, sold, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    publisher = db.relationship('User', backref=db.backref('marketplace_offers', lazy=True, cascade='all, delete-orphan'))

    @property
    def status_label(self):
        return {'available': 'Disponible', 'sold': 'Vendu', 'expired': 'Expiré'}.get(self.status, 'Inconnu')

    @property
    def status_color(self):
        return {'available': 'success', 'sold': 'secondary', 'expired': 'danger'}.get(self.status, 'secondary')

    def __repr__(self):
        return f'<MarketplaceOffer {self.title}>'
