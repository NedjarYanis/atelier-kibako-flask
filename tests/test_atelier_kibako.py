import os
import tempfile
import unittest
from pathlib import Path

# Isoler les tests de tout .env existant
import config_manager
from app import create_app
from models import Category, Order, Product, db


class AtelierKibakoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.orig_env_path = config_manager.ENV_PATH
        self.orig_sqlite_path = config_manager.DEFAULT_SQLITE_PATH
        self.orig_sqlite_uri = config_manager.DEFAULT_SQLITE_URI

        tmp_path = Path(self.tmp_dir.name)
        config_manager.ENV_PATH = tmp_path / ".env"
        config_manager.DEFAULT_SQLITE_PATH = tmp_path / "test_kibako.db"
        config_manager.DEFAULT_SQLITE_URI = f"sqlite:///{config_manager.DEFAULT_SQLITE_PATH}"

        # Patch également dans app module
        import app as app_module
        app_module.DEFAULT_SQLITE_URI = config_manager.DEFAULT_SQLITE_URI

        os.environ.pop("DATABASE_URI", None)
        os.environ.pop("DB_MODE", None)

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            for eng in db.engines.values():
                eng.dispose()
        config_manager.ENV_PATH = self.orig_env_path
        config_manager.DEFAULT_SQLITE_PATH = self.orig_sqlite_path
        config_manager.DEFAULT_SQLITE_URI = self.orig_sqlite_uri
        self.tmp_dir.cleanup()

    def test_uri_normalization(self):
        self.assertEqual(
            config_manager.normalize_db_uri("mariadb://u:p@localhost:3306/kibako"),
            "mysql+pymysql://u:p@localhost:3306/kibako?charset=utf8mb4",
        )
        self.assertEqual(
            config_manager.normalize_db_uri("mysql://u:p@127.0.0.1/kibako"),
            "mysql+pymysql://u:p@127.0.0.1/kibako?charset=utf8mb4",
        )
        with self.assertRaises(ValueError):
            config_manager.normalize_db_uri("postgres://u:p@localhost/db")

    def test_setup_test_db_and_hot_swap_save(self):
        # Page /setup accessible
        res = self.client.get("/setup")
        self.assertEqual(res.status_code, 200)

        # Test SQLite local
        res_test = self.client.post("/api/setup/test-db", json={"mode": "sqlite"})
        self.assertEqual(res_test.status_code, 200)
        data = res_test.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("SQLite", data["version"])

        # Test MariaDB inaccessible -> conseil en français
        res_bad = self.client.post(
            "/api/setup/test-db",
            json={
                "mode": "fields",
                "host": "127.0.0.1",
                "port": 33999,
                "database": "atelier_kibako",
                "user": "kibako",
                "password": "secret",
            },
        )
        self.assertEqual(res_bad.status_code, 400)
        bad_data = res_bad.get_json()
        self.assertFalse(bad_data["ok"])
        self.assertIn("Impossible de joindre", bad_data["advice"])

        # Sauvegarde & Initialisation ORM (bascule à chaud + seed)
        res_save = self.client.post(
            "/api/setup/save",
            json={"mode": "sqlite", "seed_demo": True},
        )
        self.assertEqual(res_save.status_code, 200)
        save_data = res_save.get_json()
        self.assertTrue(save_data["ok"])
        self.assertEqual(save_data["categories_created"], 4)
        self.assertEqual(save_data["products_created"], 8)

    def test_full_ecommerce_flow(self):
        # Initialiser via /api/setup/save
        self.client.post("/api/setup/save", json={"mode": "sqlite", "seed_demo": True})

        # Accueil & Catalogue & Filtres
        self.assertEqual(self.client.get("/").status_code, 200)
        res_cat = self.client.get("/catalogue?q=Totoro")
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b"Totoro", res_cat.data)

        # Fiche produit
        res_prod = self.client.get("/produit/mon-voisin-totoro-path-of-the-wind")
        self.assertEqual(res_prod.status_code, 200)
        self.assertIn(b"Path of the Wind", res_prod.data)

        with self.app.app_context():
            totoro = Product.query.filter_by(slug="mon-voisin-totoro-path-of-the-wind").first()
            initial_stock = totoro.stock
            totoro_id = totoro.id

        # Ajout panier -> Frais de port offerts (>= 80 EUR car Totoro = 89 EUR)
        res_add = self.client.post(
            "/panier/ajouter",
            data={"product_id": totoro_id, "quantity": 2},
            follow_redirects=True,
        )
        self.assertEqual(res_add.status_code, 200)
        res_cart = self.client.get("/panier")
        self.assertIn(b"Offerts", res_cart.data)

        # Validation commande en transaction ORM
        res_checkout = self.client.post(
            "/commande/valider",
            data={
                "customer_name": "Yanis Nedjar",
                "customer_email": "yanis@example.com",
                "shipping_address": "10 rue du Bois",
                "postal_code": "75011",
                "city": "Paris",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_checkout.status_code, 200)
        self.assertIn(b"KBK-", res_checkout.data)

        with self.app.app_context():
            totoro_after = db.session.get(Product, totoro_id)
            self.assertEqual(totoro_after.stock, initial_stock - 2)
            order = Order.query.first()
            self.assertIsNotNone(order)
            order_id = order.id

        # Admin: ajout produit, suppression produit, mise à jour statut commande
        res_admin = self.client.get("/admin")
        self.assertEqual(res_admin.status_code, 200)

        with self.app.app_context():
            cat_id = Category.query.first().id

        res_new_prod = self.client.post(
            "/admin/produits/ajouter",
            data={
                "name": "Kibako Test",
                "universe": "Ghibli",
                "melody_title": "Test Tune",
                "wood_type": "Noyer",
                "mechanism": "18 lames",
                "price": "45.00",
                "stock": "5",
                "category_id": cat_id,
                "description": "Produit de test",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_new_prod.status_code, 200)
        self.assertIn(b"Kibako Test", res_new_prod.data)

        with self.app.app_context():
            added = Product.query.filter_by(name="Kibako Test").first()
            added_id = added.id

        res_del = self.client.post(f"/admin/produits/{added_id}/supprimer", follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)

        res_status = self.client.post(
            f"/admin/commandes/{order_id}/statut",
            data={"status": "Expédiée"},
            follow_redirects=True,
        )
        self.assertEqual(res_status.status_code, 200)
        with self.app.app_context():
            self.assertEqual(db.session.get(Order, order_id).status, "Expédiée")

        # API v1 REST & Télémétrie Chart.js
        res_health = self.client.get("/api/v1/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertTrue(res_health.get_json()["db_ready"])

        res_prods_api = self.client.get("/api/v1/products")
        self.assertEqual(res_prods_api.status_code, 200)
        self.assertEqual(res_prods_api.get_json()["count"], 8)

        res_tel = self.client.get("/api/v1/telemetry")
        self.assertEqual(res_tel.status_code, 200)
        self.assertTrue(res_tel.get_json()["ok"])


if __name__ == "__main__":
    unittest.main()
