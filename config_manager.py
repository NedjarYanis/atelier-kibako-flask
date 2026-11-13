import os
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse, urlunparse, parse_qs, urlencode

import pymysql
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_SQLITE_PATH = INSTANCE_DIR / "atelier_kibako.db"
DEFAULT_SQLITE_URI = f"sqlite:///{DEFAULT_SQLITE_PATH}"


def normalize_db_uri(raw_uri: str) -> str:
    """Normalise une URI MariaDB/MySQL/SQLite vers le format SQLAlchemy 2.x."""
    uri = (raw_uri or "").strip()
    if not uri:
        raise ValueError("L'URI de base de données ne peut pas être vide.")

    if uri.startswith("sqlite:///") or uri == "sqlite:///:memory:":
        return uri

    if uri.startswith("mariadb+pymysql://"):
        uri = "mysql+pymysql://" + uri[len("mariadb+pymysql://"):]
    elif uri.startswith("mariadb://"):
        uri = "mysql+pymysql://" + uri[len("mariadb://"):]
    elif uri.startswith("mysql://"):
        uri = "mysql+pymysql://" + uri[len("mysql://"):]
    elif not uri.startswith("mysql+pymysql://"):
        raise ValueError(
            "Schéma d'URI non supporté. Utilisez mariadb://, mysql://, mysql+pymysql:// ou sqlite:///."
        )

    parsed = urlparse(uri)
    if not parsed.hostname:
        raise ValueError("L'hôte est manquant dans l'URI de connexion.")
    db_name = parsed.path.lstrip("/")
    if not db_name:
        raise ValueError("Le nom de la base de données est manquant dans l'URI.")

    query_params = parse_qs(parsed.query)
    if "charset" not in query_params:
        query_params["charset"] = ["utf8mb4"]
    new_query = urlencode(query_params, doseq=True)

    return urlunparse(
        (
            "mysql+pymysql",
            parsed.netloc,
            f"/{db_name}",
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


def build_mariadb_uri(
    host: str,
    port: str | int,
    database: str,
    user: str,
    password: str = "",
) -> str:
    """Construit une URI mysql+pymysql:// encodée proprement."""
    host = (host or "127.0.0.1").strip()
    port_str = str(port or "3306").strip()
    database = (database or "atelier_kibako").strip()
    user = (user or "root").strip()

    if not re.fullmatch(r"\d+", port_str):
        raise ValueError("Le port doit être un nombre entier (ex. 3306).")
    if not re.fullmatch(r"[A-Za-z0-9_$-]+", database):
        raise ValueError(
            "Nom de base invalide. Utilisez uniquement des lettres, chiffres, tirets ou underscores."
        )

    encoded_user = quote_plus(user)
    if password:
        encoded_pass = quote_plus(password)
        auth = f"{encoded_user}:{encoded_pass}"
    else:
        auth = encoded_user

    return f"mysql+pymysql://{auth}@{host}:{port_str}/{database}?charset=utf8mb4"


def parse_mariadb_uri(uri: str) -> dict:
    """Extrait les paramètres de connexion d'une URI mysql+pymysql://."""
    normalized = normalize_db_uri(uri)
    parsed = urlparse(normalized)
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": parsed.path.lstrip("/"),
    }


def _french_mariadb_error_advice(exc: Exception, params: dict) -> str:
    """Traduit les erreurs PyMySQL courantes en conseils clairs en français."""
    msg = str(exc)
    code = exc.args[0] if getattr(exc, "args", None) and isinstance(exc.args[0], int) else None

    if code == 1045 or "Access denied" in msg:
        return (
            f"Accès refusé pour l'utilisateur '{params['user']}' sur {params['host']}. "
            "Vérifiez le mot de passe ou exécutez : "
            f"GRANT ALL PRIVILEGES ON `{params['database']}`.* TO '{params['user']}'@'localhost';"
        )
    if code == 2003 or "Can't connect" in msg or "Connection refused" in msg:
        return (
            f"Impossible de joindre MariaDB sur {params['host']}:{params['port']}. "
            "Vérifiez que le service MariaDB est démarré (sudo systemctl start mariadb) "
            "et que le port est accessible."
        )
    if code == 2005 or "Name or service not known" in msg or "getaddrinfo failed" in msg:
        return (
            f"Nom d'hôte '{params['host']}' introuvable. "
            "Vérifiez l'adresse IP ou le nom de domaine du serveur."
        )
    if "cryptography" in msg.lower():
        return (
            "Le module 'cryptography' est requis pour l'authentification MariaDB/MySQL. "
            "Installez-le avec pip install cryptography."
        )
    if "timed out" in msg.lower():
        return (
            f"Délai de connexion dépassé vers {params['host']}:{params['port']}. "
            "Vérifiez le pare-feu ou la configuration bind-address de MariaDB."
        )
    return f"Erreur de connexion MariaDB : {msg}"


def test_database_connection(raw_uri: str) -> dict:
    """Teste une connexion MariaDB ou SQLite et retourne version, latence et diagnostic."""
    try:
        uri = normalize_db_uri(raw_uri)
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "advice": "Vérifiez le format de l'URI saisie."}

    start = time.perf_counter()

    if uri.startswith("sqlite://"):
        try:
            if uri == "sqlite:///:memory:":
                conn = sqlite3.connect(":memory:")
            else:
                db_path = Path(uri[len("sqlite:///"):])
                db_path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(db_path))
            version = conn.execute("SELECT sqlite_version()").fetchone()[0]
            conn.close()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "ok": True,
                "dialect": "SQLite (Aperçu Local)",
                "version": f"SQLite {version}",
                "latency_ms": latency_ms,
                "database_exists": True,
                "normalized_uri": uri,
                "message": "Base SQLite prête pour l'aperçu local immédiat.",
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "advice": "Vérifiez les permissions d'écriture dans le dossier instance/.",
            }

    params = parse_mariadb_uri(uri)
    try:
        conn = pymysql.connect(
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            connect_timeout=5,
            charset="utf8mb4",
        )
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            cur.execute("SHOW DATABASES LIKE %s", (params["database"],))
            db_exists = cur.fetchone() is not None
        conn.close()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        note = (
            f"La base '{params['database']}' existe déjà."
            if db_exists
            else f"La base '{params['database']}' n'existe pas encore : elle sera créée automatiquement."
        )
        return {
            "ok": True,
            "dialect": "MariaDB / MySQL",
            "version": str(version),
            "latency_ms": latency_ms,
            "database_exists": db_exists,
            "normalized_uri": uri,
            "message": f"Connexion au serveur réussie ! {note}",
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": str(exc),
            "advice": _french_mariadb_error_advice(exc, params),
        }


def ensure_database_exists(raw_uri: str) -> str:
    """Crée la base MariaDB si elle n'existe pas encore, ou prépare le dossier SQLite."""
    uri = normalize_db_uri(raw_uri)
    if uri.startswith("sqlite:///"):
        db_path = Path(uri[len("sqlite:///"):])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return uri
    if uri == "sqlite:///:memory:":
        return uri

    params = parse_mariadb_uri(uri)
    conn = pymysql.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        connect_timeout=5,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            safe_db = params["database"].replace("`", "")
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{safe_db}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()
    return uri


def load_env_config() -> dict:
    """Lit la configuration courante depuis .env ou l'environnement."""
    env_vals = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    raw_uri = env_vals.get("DATABASE_URI") or os.environ.get("DATABASE_URI") or ""
    secret_key = env_vals.get("SECRET_KEY") or os.environ.get("SECRET_KEY") or "atelier-kibako-dev-secret-key"
    db_mode = env_vals.get("DB_MODE") or ("sqlite" if raw_uri.startswith("sqlite") else "mariadb" if raw_uri else "unconfigured")

    if raw_uri:
        try:
            normalized_uri = normalize_db_uri(raw_uri)
        except ValueError:
            normalized_uri = DEFAULT_SQLITE_URI
            db_mode = "sqlite"
    else:
        normalized_uri = DEFAULT_SQLITE_URI

    return {
        "configured": bool(raw_uri),
        "db_mode": db_mode,
        "database_uri": normalized_uri,
        "secret_key": secret_key,
    }


def save_env_config(uri: str, db_mode: str = "mariadb") -> dict:
    """Enregistre la configuration dans .env et met à jour os.environ."""
    normalized = normalize_db_uri(uri)
    existing = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    secret_key = existing.get("SECRET_KEY") or os.environ.get("SECRET_KEY") or os.urandom(24).hex()

    lines = [
        "# Configuration générée visuellement par Atelier Kibako (/setup)",
        f"SECRET_KEY={secret_key}",
        f"DB_MODE={db_mode}",
        f"DATABASE_URI={normalized}",
        "",
    ]
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")

    os.environ["SECRET_KEY"] = secret_key
    os.environ["DB_MODE"] = db_mode
    os.environ["DATABASE_URI"] = normalized

    return {
        "configured": True,
        "db_mode": db_mode,
        "database_uri": normalized,
        "secret_key": secret_key,
    }


def mask_uri(uri: str) -> str:
    """Masque le mot de passe dans une URI pour l'affichage UI."""
    if not uri or uri.startswith("sqlite"):
        return uri
    try:
        parsed = urlparse(uri)
        if parsed.password:
            netloc = f"{parsed.username}:••••••@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    except Exception:
        pass
    return uri
