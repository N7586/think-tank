from flask import Blueprint

reseau_bp = Blueprint('reseau', __name__, url_prefix='/reseau')

from app.reseau import routes
