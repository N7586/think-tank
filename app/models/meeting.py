import uuid
from datetime import datetime
from app.extensions import db


class Meeting(db.Model):
    __tablename__ = 'meetings'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    room_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='active')  # active, ended, cancelled
    max_participants = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)

    host = db.relationship('User', backref=db.backref('hosted_meetings', lazy=True, cascade='all, delete-orphan'))
    participants = db.relationship('MeetingParticipant', backref='meeting', lazy=True, cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def active_participants_count(self):
        return MeetingParticipant.query.filter_by(
            meeting_id=self.id, is_kicked=False
        ).filter(MeetingParticipant.left_at.is_(None)).count()

    @property
    def status_label(self):
        return {'active': 'En cours', 'terminee': 'Terminee', 'annulee': 'Annulee'}.get(self.status, 'Inconnu')

    @property
    def status_color(self):
        return {'active': 'success', 'terminee': 'secondary', 'annulee': 'danger'}.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Meeting {self.title}>'


class MeetingParticipant(db.Model):
    __tablename__ = 'meeting_participants'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='participant')  # host, moderator, participant
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    left_at = db.Column(db.DateTime, nullable=True)
    is_kicked = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('meeting_participations', lazy=True, cascade='all, delete-orphan'))

    @property
    def is_online(self):
        return self.left_at is None and not self.is_kicked

    @property
    def role_label(self):
        return {'host': 'Organisateur', 'moderator': 'Moderateur', 'participant': 'Participant'}.get(self.role, 'Participant')

    def __repr__(self):
        return f'<MeetingParticipant {self.user_id} in {self.meeting_id}>'
