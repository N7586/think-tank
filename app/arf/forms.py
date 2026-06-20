from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class CreateARFForm(FlaskForm):
    name = StringField('Nom de l\'ARF', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Description', validators=[DataRequired()])
    sector = SelectField('Secteur', choices=[
        ('agro-industrie', 'Agro-industrie'),
        ('mines', 'Mines'),
        ('energie', 'Énergie'),
        ('numérique', 'Numérique'),
        ('infrastructure', 'Infrastructure'),
        ('santé', 'Santé'),
        ('education', 'Éducation'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
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


class SubscribeForm(FlaskForm):
    units = StringField('Nombre de tikecs', validators=[DataRequired()])
    payment_method = SelectField('Méthode de paiement', choices=[
        ('orange_money', 'Orange Money'),
        ('mtn_momo', 'MTN MoMo')
    ], validators=[DataRequired()])
    phone_number = StringField('Numéro de téléphone', validators=[DataRequired(), Length(min=9, max=20)])
    submit = SubmitField('Souscrire')
