from flask import Blueprint

seller_bp = Blueprint('seller', __name__)

from app.seller import routes