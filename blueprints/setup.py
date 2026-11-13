from flask import Blueprint, current_app, jsonify, render_template, request

import config_manager
from config_manager import (
    build_mariadb_uri,
    ensure_database_exists,
    mask_uri,
    normalize_db_uri,
    save_env_config,
    test_database_connection,
)
from models import seed_catalog

setup_bp = Blueprint("setup", __name__)


def _extract_uri_from_payload(data: dict) -> tuple[str, str]:
    mode = (data.get("mode") or "fields").strip()
    if mode == "sqlite":
        return config_manager.DEFAULT_SQLITE_URI, "sqlite"
    if mode == "uri":
        raw_uri = data.get("uri", "")
        return normalize_db_uri(raw_uri), "mariadb"
    uri = build_mariadb_uri(
        host=data.get("host", "127.0.0.1"),
        port=data.get("port", 3306),
        database=data.get("database", "atelier_kibako"),
        user=data.get("user", "root"),
        password=data.get("password", ""),
    )
    return uri, "mariadb"


@setup_bp.route("/setup")
def setup_page():
    return render_template("setup.html")


@setup_bp.route("/api/setup/test-db", methods=["POST"])
def api_setup_test_db():
    data = request.get_json(silent=True) or {}
    try:
        uri, _ = _extract_uri_from_payload(data)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc), "advice": "Vérifiez les paramètres saisis."}), 400

    result = test_database_connection(uri)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


@setup_bp.route("/api/setup/save", methods=["POST"])
def api_setup_save():
    data = request.get_json(silent=True) or {}
    seed_demo = bool(data.get("seed_demo", True))

    try:
        uri, db_mode = _extract_uri_from_payload(data)
        ensure_database_exists(uri)
        save_env_config(uri, db_mode=db_mode)
        current_app.extensions["hot_swap_engine"](uri, db_mode=db_mode)

        cats_created, prods_created = (0, 0)
        if seed_demo:
            with current_app.app_context():
                cats_created, prods_created = seed_catalog()

        return jsonify(
            {
                "ok": True,
                "message": "Configuration enregistrée, schéma ORM créé et moteur SQLAlchemy basculé à chaud.",
                "db_mode": db_mode,
                "masked_uri": mask_uri(uri),
                "seeded": seed_demo,
                "categories_created": cats_created,
                "products_created": prods_created,
            }
        )
    except Exception as exc:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": str(exc),
                    "advice": "Testez d'abord la connexion pour diagnostiquer les droits ou l'hôte MariaDB.",
                }
            ),
            400,
        )
