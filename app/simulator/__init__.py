from flask import Blueprint

simulator_bp = Blueprint('simulator', __name__, url_prefix='/simulator')

from app.simulator import routes
