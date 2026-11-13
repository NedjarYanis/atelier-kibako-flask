# Atelier Kibako — E-Commerce Flask & SQLAlchemy 2.x

Boutique artisanale de boîtes à musique en bois massif inspirées des univers **Pop Culture, Manga, Studio Ghibli, Jeux Vidéo et Cinéma**.
L'application est construite avec **Flask**, **SQLAlchemy 2.x** (connecté à **MariaDB** via PyMySQL ou **SQLite** en aperçu local), un **simulateur acoustique Web Audio API** et une **configuration 100 % visuelle** via `/setup`.

---

## Stack Technique

- **Backend** : Python 3.11+, Flask 3.x, Flask-SQLAlchemy 3.1+, SQLAlchemy 2.x
- **Base de données** : MariaDB / MySQL (`PyMySQL` + `cryptography`) ou SQLite (mode aperçu local)
- **Configuration** : `python-dotenv` piloté visuellement depuis `/setup` (bascule du moteur ORM à chaud)
- **Frontend** : HTML5 sémantique, Vanilla CSS (design system bois & papier *washi*), JavaScript natif (`Web Audio API` pour la synthèse des lames de boîte à musique)

---

## Installation (Linux / macOS / Windows)

### 1. Cloner le dépôt

```bash
git clone https://github.com/NedjarYanis/atelier-kibako-flask.git
cd atelier-kibako-flask
```

### 2. Créer l'environnement virtuel et installer les dépendances

**Linux / macOS :**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell) :**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Lancer l'application

```bash
python app.py
```

L'application démarre sur `http://127.0.0.1:5000` **même si MariaDB n'est pas encore configuré**.

---

## Guide Visuel de Configuration (`/setup`)

Rendez-vous sur `http://127.0.0.1:5000/setup` pour configurer votre base de données sans éditer de fichier à la main.

Trois modes sont disponibles :

1. **Champs MariaDB** : renseignez Hôte (`127.0.0.1`), Port (`3306`), Nom de la base (`atelier_kibako`), Utilisateur et Mot de passe (avec bouton *Afficher / Masquer*).
2. **Lien / URI direct** : collez une URI `mariadb://...`, `mysql://...` ou `mysql+pymysql://...` — elle est automatiquement normalisée vers `mysql+pymysql://...?charset=utf8mb4`.
3. **Aperçu Local (SQLite)** : crée instantanément une base locale `instance/atelier_kibako.db` pour tester toute la boutique sans serveur MariaDB.

### Actions disponibles sur `/setup`
- **Tester la connexion** (`POST /api/setup/test-db`) : mesure la latence en ms, affiche la version du serveur MariaDB/SQLite et fournit des conseils de dépannage en français en cas d'erreur (`Access denied`, port fermé, hôte introuvable…).
- **Sauvegarder & Initialiser l'ORM** (`POST /api/setup/save`) :
  - Exécute `CREATE DATABASE IF NOT EXISTS` sur MariaDB si la base n'existe pas encore ;
  - Écrit le fichier `.env` ;
  - Bascule le moteur SQLAlchemy **à chaud sans redémarrer Flask** ;
  - Exécute `db.create_all()` ;
  - Peuple le catalogue de démo (`seed_catalog()`) : **4 catégories** et **8 boîtes à musique** (*Naruto*, *One Piece*, *Mon Voisin Totoro*, *Zelda*, *Harry Potter*, *Demon Slayer*, *Le Château Ambulant*, *L'Attaque des Titans*).

---

## Schéma ORM (`models.py`)

| Modèle | Table | Colonnes principales |
| :--- | :--- | :--- |
| `Category` | `categories` | `id`, `name`, `slug`, `description` |
| `Product` | `products` | `id`, `name`, `slug`, `universe`, `melody_title`, `melody_notes` (`JSON`), `wood_type`, `mechanism`, `price`, `stock`, `image_url`, `description`, `featured`, `category_id`, `created_at` |
| `Order` | `orders` | `id`, `order_number`, `customer_name`, `customer_email`, `shipping_address`, `city`, `postal_code`, `total_amount`, `status`, `created_at` |
| `OrderItem` | `order_items` | `id`, `order_id`, `product_id`, `quantity`, `unit_price` |

---

## Routes & APIs

| Route | Méthode(s) | Rôle |
| :--- | :--- | :--- |
| `/` | `GET` | Accueil (hero, pièces vedettes, univers, savoir-faire) |
| `/catalogue` | `GET` | Recherche (`q`) et filtres (`category`, `universe`, `wood`, `mechanism`, `sort`) |
| `/produit/<slug>` | `GET` | Fiche produit + lecteur audio Web Audio API (`musicbox.js`) |
| `/panier` | `GET` | Panier session + frais de port offerts dès 80 € |
| `/panier/ajouter` | `POST` | Ajout au panier |
| `/panier/modifier` | `POST` | Mise à jour quantité |
| `/panier/supprimer/<id>` | `POST` | Suppression d'un article |
| `/commande/valider` | `GET`, `POST` | Validation de commande en transaction ORM avec décrémentation du stock |
| `/commande/confirmation/<order_number>` | `GET` | Récapitulatif de commande confirmée |
| `/setup` | `GET` | Interface visuelle de configuration BDD |
| `/api/setup/test-db` | `POST` | Diagnostic de connexion (version, latence, conseils FR) |
| `/api/setup/save` | `POST` | Sauvegarde `.env`, création BDD, bascule à chaud & seed |
| `/admin` | `GET` | Tableau de bord Atelier (produits & commandes) |
| `/admin/produits/ajouter` | `POST` | Ajout d'un produit |
| `/admin/produits/<id>/supprimer` | `POST` | Suppression d'un produit |
| `/admin/commandes/<id>/statut` | `POST` | Mise à jour du statut d'une commande |

---

## Structure du Projet

```text
atelier-kibako-flask/
├── app.py                  # Application Flask, routes boutique, admin & APIs /setup
├── config_manager.py       # Normalisation URI, test MariaDB/SQLite, écriture .env
├── models.py               # Modèles SQLAlchemy 2.x + seed_catalog()
├── requirements.txt        # Dépendances Python
├── README.md               # Documentation du projet
├── static/
│   ├── css/style.css       # Design system artisanal bois & washi
│   ├── images/             # Visuels des boîtes à musique et de l'atelier
│   └── js/
│       ├── musicbox.js     # Synthétiseur Web Audio API des lames en laiton
│       └── setup.js        # Logique interactive de /setup
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── catalogue.html
│   ├── product.html
│   ├── cart.html
│   ├── checkout.html
│   ├── order_confirmation.html
│   ├── setup.html
│   └── admin.html
└── tests/
    └── test_atelier_kibako.py
```

---

## Tests Automatisés

```bash
.venv/bin/python -m unittest discover -s tests -v
```
