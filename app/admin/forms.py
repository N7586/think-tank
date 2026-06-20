from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class CreateARFForm(FlaskForm):
    name = StringField('Nom ARF', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Description', validators=[DataRequired()])
    sector = StringField('Secteur', validators=[DataRequired(), Length(max=100)])
    country = StringField('Pays', validators=[DataRequired(), Length(max=100)])
    total_value = StringField('Valeur totale (€)', validators=[DataRequired()])
    unit_price = StringField('Prix par tikec (€)', validators=[DataRequired()])
    expected_return = StringField('Rendement attendu (%)', validators=[DataRequired()])
    risk_level = SelectField('Niveau de risque', choices=[
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé')
    ])
    submit = SubmitField('Créer l\'ARF')
