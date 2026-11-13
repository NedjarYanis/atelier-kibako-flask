from blueprints.admin import admin_bp
from blueprints.api import api_bp
from blueprints.cart import cart_bp
from blueprints.setup import setup_bp
from blueprints.shop import shop_bp


def register_blueprints(app):
    """Enregistre tous les Blueprints modulaires de l'application Atelier Kibako."""
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
