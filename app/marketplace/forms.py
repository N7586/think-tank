from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length


class MarketplaceOfferForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Description', validators=[DataRequired()])
    contract_type = SelectField('Type de contrat', choices=[
        ('marche-public', 'Marché public'),
        ('appel-offres', 'Appel d\'offres'),
        ('prestation', 'Prestation de services'),
        ('fourniture', 'Fourniture'),
        ('travaux', 'Travaux publics'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
    value = StringField('Valeur du droit (€)', validators=[DataRequired()])
    deadline = StringField('Échéance (optionnel)')
    submit = SubmitField('Publier l\'offre')
