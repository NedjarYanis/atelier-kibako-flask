from flask import Flask, request, session
from sqlalchemy import inspect, text

import config_manager
from blueprints import register_blueprints
from blueprints.cart import FREE_SHIPPING_THRESHOLD
from config_manager import ensure_database_exists, load_env_config, mask_uri
from models import Category, db
from themes import SITES, SITES_ORDER


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = load_env_config()

    app.config["SECRET_KEY"] = cfg["secret_key"]
    app.config["SQLALCHEMY_DATABASE_URI"] = cfg["database_uri"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["DB_CONFIGURED"] = cfg["configured"]
    app.config["DB_MODE"] = cfg["db_mode"]

    db.init_app(app)

    def check_db_ready() -> tuple[bool, str | None]:
        """Vérifie sans planter si la base est joignable et si les tables existent."""
        try:
            with app.app_context():
                db.session.execute(text("SELECT 1"))
                inspector = inspect(db.engine)
                has_tables = inspector.has_table("products") and inspector.has_table("categories")
                if not has_tables:
                    return False, "Tables ORM non initialisées. Rendez-vous sur /setup pour initialiser le catalogue."
                return True, None
        except Exception as exc:
            return False, f"Base de données non connectée : {exc}"

    def hot_swap_engine(new_uri: str, db_mode: str) -> None:
        """Bascule le moteur SQLAlchemy à chaud sans redémarrer Flask."""
        with app.app_context():
            db.session.remove()
            try:
                for eng in db.engines.values():
                    eng.dispose()
            except Exception:
                pass

            app.config["SQLALCHEMY_DATABASE_URI"] = new_uri
            app.config["DB_CONFIGURED"] = True
            app.config["DB_MODE"] = db_mode

            options = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {})
            options["url"] = new_uri
            new_engine = db._make_engine(None, options, app)
            db._app_engines.setdefault(app, {})[None] = new_engine

            db.create_all()

    app.extensions["check_db_ready"] = check_db_ready
    app.extensions["hot_swap_engine"] = hot_swap_engine

    # Initialisation douce au démarrage : ne plante jamais si MariaDB est absent
    with app.app_context():
        if cfg["configured"]:
            try:
                db.session.execute(text("SELECT 1"))
            except Exception:
                pass
        else:
            try:
                ensure_database_exists(config_manager.DEFAULT_SQLITE_URI)
                db.create_all()
            except Exception:
                pass

    @app.context_processor
    def inject_globals():
        cart = session.get("cart", {})
        cart_count = sum(int(qty) for qty in cart.values()) if isinstance(cart, dict) else 0
        db_ok, db_msg = check_db_ready()
        categories_nav = []
        if db_ok:
            try:
                categories_nav = Category.query.order_by(Category.name.asc()).all()
            except Exception:
                categories_nav = []
        active_theme = None
        if request.view_args and "theme" in request.view_args:
            active_theme = request.view_args.get("theme")
        return {
            "cart_count": cart_count,
            "db_status": {
                "ready": db_ok,
                "message": db_msg,
                "configured": app.config.get("DB_CONFIGURED", False),
                "mode": app.config.get("DB_MODE", "unconfigured"),
                "masked_uri": mask_uri(app.config.get("SQLALCHEMY_DATABASE_URI", "")),
            },
            "categories_nav": categories_nav,
            "free_shipping_threshold": FREE_SHIPPING_THRESHOLD,
            "all_sites": [SITES[k] for k in SITES_ORDER],
            "active_theme": active_theme,
        }

    register_blueprints(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
