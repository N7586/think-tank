from datetime import datetime
from app.extensions import db


class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(10), nullable=False, default='pending')  # pending, published, archived, rejected
    admin_comment = db.Column(db.Text, nullable=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)

    author = db.relationship('User', backref=db.backref('articles', lazy=True, cascade='all, delete-orphan'))

    @property
    def status_label(self):
        return {
            'pending': 'En attente',
            'published': 'Publie',
            'archived': 'Archive',
            'rejected': 'Rejete'
        }.get(self.status, 'Inconnu')

    @property
    def status_color(self):
        return {
            'pending': 'warning',
            'published': 'success',
            'archived': 'secondary',
            'rejected': 'danger'
        }.get(self.status, 'secondary')

    @property
    def excerpt(self):
        return (self.content[:200] + '...') if len(self.content) > 200 else self.content

    def __repr__(self):
        return f'<Article {self.title}>'
