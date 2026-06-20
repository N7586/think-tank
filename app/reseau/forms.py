from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class MeetingForm(FlaskForm):
    title = StringField('Titre de la reunion', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Description (optionnel)')
    submit = SubmitField('Demarrer la reunion')


class ArticleForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(min=3, max=255)])
    content = TextAreaField('Contenu', validators=[DataRequired(), Length(min=10)])
    category = SelectField('Categorie', choices=[
        ('investissement', 'Investissement'),
        ('finance', 'Finance'),
        ('economie', 'Economie'),
        ('dveloppement', 'Developpement durable'),
        ('actualite', 'Actualite'),
        ('tutorial', 'Tutoriel'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
    submit = SubmitField('Soumettre l\'article')
