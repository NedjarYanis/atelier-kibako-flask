# Atelier Kibako — E-Commerce Flask & SQLAlchemy 2.x

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white" alt="Flask" /></a>
  <a href="https://www.sqlalchemy.org/"><img src="https://img.shields.io/badge/SQLAlchemy-2.x-red?logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" /></a>
  <a href="https://mariadb.org/"><img src="https://img.shields.io/badge/MariaDB-Supported-003545?logo=mariadb&logoColor=white" alt="MariaDB" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licence-MIT-green" alt="Licence" /></a>
</p>

<br/>

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

---

## Fonctionnalités de la Boutique

- **Catalogue Interactif & Filtres** : Recherche et filtrage par univers (Ghibli, Zelda, Mario, Anime).
- **Simulateur Acoustique Web Audio API** : Écoute d'un extrait de mélodie généré en temps réel via des oscillateurs Web Audio.
- **Panier & Gestion des Commandes** : Ajout d'articles, gestion des quantités et récapitulatif de commande.
- **Administration & Gestion des Stocks** : Tableau de bord simple pour ajouter, modifier ou désactiver des modèles.

---

## Auteur

Développé par **[Yanis Nedjar](https://github.com/NedjarYanis)** — BUT Informatique @ IUT d'Orléans.
