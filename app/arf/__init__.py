from flask import Blueprint

arf_bp = Blueprint('arf', __name__, url_prefix='/arf')

from app.arf import routes
