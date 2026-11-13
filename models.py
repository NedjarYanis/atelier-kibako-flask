from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)

    products = db.relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category {self.slug}>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), nullable=False, unique=True, index=True)
    universe = db.Column(db.String(100), nullable=False, index=True)
    melody_title = db.Column(db.String(160), nullable=False)
    melody_notes = db.Column(db.JSON, nullable=False, default=list)
    wood_type = db.Column(db.String(100), nullable=False)
    mechanism = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=10)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    featured = db.Column(db.Boolean, nullable=False, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    category = db.relationship("Category", back_populates="products")
    order_items = db.relationship("OrderItem", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.slug}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(40), nullable=False, unique=True, index=True)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    shipping_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="En attente")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id} product={self.product_id}>"


# Fréquences de notes (Hz) pour les mélodies Web Audio API
_NOTES = {
    "C4": 261.63, "D4": 293.66, "Eb4": 311.13, "E4": 329.63, "F4": 349.23,
    "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "Bb4": 466.16,
    "B4": 493.88, "C5": 523.25, "C#5": 554.37, "D5": 587.33, "Eb5": 622.25,
    "E5": 659.25, "F5": 698.46, "F#5": 739.99, "G5": 783.99, "G#5": 830.61,
    "A5": 880.00, "Bb5": 932.33, "B5": 987.77, "C6": 1046.50,
}


def _seq(pairs: list[tuple[str, float]]) -> list[dict]:
    return [{"note": n, "freq": _NOTES[n], "dur": d} for n, d in pairs]


def seed_catalog() -> tuple[int, int]:
    """Peuple les 4 catégories et les 8 boîtes à musique Pop Culture & Manga de démonstration."""
    categories_data = [
        {
            "name": "Manga & Shōnen",
            "slug": "manga-shonen",
            "description": "Boîtes à musique sculptées aux motifs des grands classiques de l'animation japonaise.",
        },
        {
            "name": "Studio Ghibli",
            "slug": "studio-ghibli",
            "description": "Essences de noyer et d'érable abritant les mélodies poétiques de Joe Hisaishi.",
        },
        {
            "name": "Jeux Vidéo",
            "slug": "jeux-video",
            "description": "Cylindres en laiton accordés sur les thèmes légendaires du jeu vidéo.",
        },
        {
            "name": "Cinéma & Fantastique",
            "slug": "cinema-fantastique",
            "description": "Coffrets de bois sombres et marqueterie céleste pour les grandes sagas du cinéma.",
        },
    ]

    cat_map: dict[str, Category] = {}
    cats_created = 0
    for cdata in categories_data:
        cat = Category.query.filter_by(slug=cdata["slug"]).first()
        if not cat:
            cat = Category(**cdata)
            db.session.add(cat)
            cats_created += 1
        cat_map[cdata["slug"]] = cat
    db.session.flush()

    products_data = [
        {
            "name": "Kibako Konoha — Sadness and Sorrow",
            "slug": "naruto-sadness-and-sorrow",
            "universe": "Naruto",
            "melody_title": "Sadness and Sorrow",
            "melody_notes": _seq([
                ("A4", 0.45), ("E5", 0.45), ("F5", 0.45), ("E5", 0.45),
                ("D5", 0.70), ("C5", 0.35), ("B4", 0.45), ("C5", 0.45),
                ("A4", 0.85), ("E5", 0.45), ("G5", 0.45), ("F5", 0.45),
                ("E5", 0.65), ("D5", 0.40), ("C5", 0.45), ("B4", 0.85),
            ]),
            "wood_type": "Cerisier Sakura",
            "mechanism": "18 lames à remontoir",
            "price": 54.90,
            "stock": 14,
            "image_url": "/static/images/box_sakura_anime.jpg",
            "description": (
                "Façonnée en cerisier sakura du Japon à grain chaud, cette kibako arbore une gravure "
                "fine de vagues et de nuages traditionnels. Son mouvement à 18 lames restitue avec "
                "douceur la mélancolie de « Sadness and Sorrow »."
            ),
            "featured": True,
            "category_slug": "manga-shonen",
        },
        {
            "name": "Kibako Vogue Merry — Binks' Sake",
            "slug": "one-piece-binks-sake",
            "universe": "One Piece",
            "melody_title": "Binks' Sake",
            "melody_notes": _seq([
                ("G4", 0.35), ("C5", 0.45), ("D5", 0.35), ("E5", 0.50),
                ("G5", 0.45), ("E5", 0.35), ("D5", 0.45), ("C5", 0.50),
                ("D5", 0.35), ("E5", 0.35), ("G5", 0.55), ("A5", 0.45),
                ("G5", 0.40), ("E5", 0.40), ("D5", 0.45), ("C5", 0.80),
            ]),
            "wood_type": "Acajou Maritime",
            "mechanism": "18 lames à manivelle",
            "price": 59.00,
            "stock": 11,
            "image_url": "/static/images/box_mahogany_pirate.jpg",
            "description": (
                "Coffret en acajou profond incrusté d'une rose des vents et de vagues en laiton doré. "
                "L'intérieur doublé de velours bleu nuit renferme un cylindre joyeux jouant le célèbre "
                "chant des pirates « Binks' Sake »."
            ),
            "featured": True,
            "category_slug": "manga-shonen",
        },
        {
            "name": "Kibako Camphrier — Mon Voisin Totoro",
            "slug": "mon-voisin-totoro-path-of-the-wind",
            "universe": "Mon Voisin Totoro",
            "melody_title": "Path of the Wind",
            "melody_notes": _seq([
                ("E5", 0.40), ("F#5", 0.40), ("G5", 0.55), ("B5", 0.45),
                ("A5", 0.40), ("G5", 0.45), ("F#5", 0.65), ("D5", 0.40),
                ("E5", 0.40), ("F#5", 0.45), ("G5", 0.55), ("E5", 0.45),
                ("D5", 0.40), ("C5", 0.45), ("B4", 0.85),
            ]),
            "wood_type": "Noyer Kurumi",
            "mechanism": "30 lames Sankyo",
            "price": 89.00,
            "stock": 8,
            "image_url": "/static/images/box_walnut_ghibli.jpg",
            "description": (
                "Boîte à musique d'exception en noyer kurumi, ornée d'une marqueterie de laiton "
                "représentant un esprit de la forêt au cœur des feuilles de camphrier. Son mécanisme "
                "30 lames offre une résonance cristalline."
            ),
            "featured": True,
            "category_slug": "studio-ghibli",
        },
        {
            "name": "Kibako Hyrule — Zelda's Lullaby",
            "slug": "zelda-zeldas-lullaby",
            "universe": "Zelda",
            "melody_title": "Zelda's Lullaby",
            "melody_notes": _seq([
                ("B4", 0.65), ("D5", 0.35), ("A4", 0.75), ("G4", 0.35),
                ("A4", 0.35), ("B4", 0.65), ("D5", 0.35), ("A4", 0.85),
                ("B4", 0.65), ("D5", 0.35), ("A5", 0.65), ("G5", 0.35),
                ("D5", 0.70), ("C5", 0.35), ("B4", 0.35), ("A4", 0.85),
            ]),
            "wood_type": "Cyprès Hinoki",
            "mechanism": "18 lames à remontoir",
            "price": 64.90,
            "stock": 12,
            "image_url": "/static/images/box_hinoki_zelda.jpg",
            "description": (
                "Taillée dans un cyprès hinoki clair au parfum boisé apaisant, cette pièce présente "
                "des triangles géométriques incrustés à la feuille de laiton. Joue la berceuse royale "
                "d'Hyrule à chaque tour de clef."
            ),
            "featured": True,
            "category_slug": "jeux-video",
        },
        {
            "name": "Kibako Poudlard — Hedwig's Theme",
            "slug": "harry-potter-hedwigs-theme",
            "universe": "Harry Potter",
            "melody_title": "Hedwig's Theme",
            "melody_notes": _seq([
                ("B4", 0.38), ("E5", 0.55), ("G5", 0.25), ("F#5", 0.40),
                ("E5", 0.65), ("B5", 0.38), ("A5", 0.80), ("F#5", 0.75),
                ("E5", 0.55), ("G5", 0.25), ("F#5", 0.40), ("Eb5", 0.65),
                ("F5", 0.38), ("B4", 0.90),
            ]),
            "wood_type": "Chêne Ébénisé",
            "mechanism": "30 lames Sankyo",
            "price": 94.00,
            "stock": 6,
            "image_url": "/static/images/box_ebony_harrypotter.jpg",
            "description": (
                "Un coffret en chêne ébénisé sombre illuminé par des constellations dorées incrustées "
                "sous le couvercle. Le peigne 30 lames restitue avec précision les harmonies célestes "
                "du thème d'Hedwige."
            ),
            "featured": False,
            "category_slug": "cinema-fantastique",
        },
        {
            "name": "Kibako Asanoha — Kamado Tanjiro no Uta",
            "slug": "demon-slayer-kamado-tanjiro-no-uta",
            "universe": "Demon Slayer",
            "melody_title": "Kamado Tanjiro no Uta",
            "melody_notes": _seq([
                ("D5", 0.42), ("E5", 0.42), ("F#5", 0.55), ("A5", 0.45),
                ("F#5", 0.40), ("E5", 0.45), ("D5", 0.65), ("B4", 0.42),
                ("D5", 0.42), ("E5", 0.55), ("F#5", 0.45), ("E5", 0.40),
                ("D5", 0.45), ("C#5", 0.45), ("D5", 0.85),
            ]),
            "wood_type": "Bambou Torréfié",
            "mechanism": "18 lames à remontoir",
            "price": 58.00,
            "stock": 15,
            "image_url": "/static/images/box_bamboo_demonslayer.jpg",
            "description": (
                "Bambou torréfié et cèdre sombre gravés au motif japonais traditionnel asanoha "
                "(feuille de chanvre). Une caisse de résonance chaleureuse pour l'air émouvant "
                "de Tanjiro."
            ),
            "featured": False,
            "category_slug": "manga-shonen",
        },
        {
            "name": "Kibako Horloge — Merry-Go-Round of Life",
            "slug": "le-chateau-ambulant-merry-go-round-of-life",
            "universe": "Le Château Ambulant",
            "melody_title": "Merry-Go-Round of Life",
            "melody_notes": _seq([
                ("D4", 0.35), ("G4", 0.35), ("Bb4", 0.35), ("D5", 0.65),
                ("C5", 0.35), ("Bb4", 0.35), ("A4", 0.35), ("Bb4", 0.65),
                ("G4", 0.35), ("Bb4", 0.35), ("D5", 0.35), ("G5", 0.65),
                ("F5", 0.35), ("Eb5", 0.35), ("D5", 0.75),
            ]),
            "wood_type": "Érable Ondé",
            "mechanism": "30 lames Sankyo",
            "price": 98.00,
            "stock": 7,
            "image_url": "/static/images/box_maple_howl.jpg",
            "description": (
                "Érable ondé couleur miel avec marqueterie de rouages en laiton et plumes stylisées. "
                "Sa valse mécanique 30 lames capture l'élégance aérienne du Château Ambulant."
            ),
            "featured": True,
            "category_slug": "studio-ghibli",
        },
        {
            "name": "Kibako Bataillon — Shinzou wo Sasageyo!",
            "slug": "attaque-des-titans-shinzou-wo-sasageyo",
            "universe": "L'Attaque des Titans",
            "melody_title": "Shinzou wo Sasageyo!",
            "melody_notes": _seq([
                ("E4", 0.30), ("G4", 0.30), ("B4", 0.45), ("E5", 0.45),
                ("D5", 0.30), ("C5", 0.30), ("B4", 0.55), ("A4", 0.30),
                ("B4", 0.30), ("C5", 0.45), ("D5", 0.45), ("B4", 0.35),
                ("G4", 0.35), ("F#4", 0.40), ("E4", 0.80),
            ]),
            "wood_type": "Cèdre Fumé",
            "mechanism": "18 lames à remontoir",
            "price": 62.00,
            "stock": 10,
            "image_url": "/static/images/hero_atelier_kibako.jpg",
            "description": (
                "Coffret robuste en cèdre fumé assemblé à queues d'aronde apparentes. Son cylindre "
                "en laiton massif délivre les notes héroïques et solennelles de « Shinzou wo Sasageyo! »."
            ),
            "featured": False,
            "category_slug": "manga-shonen",
        },
    ]

    prods_created = 0
    for pdata in products_data:
        existing = Product.query.filter_by(slug=pdata["slug"]).first()
        if not existing:
            cat_slug = pdata.pop("category_slug")
            product = Product(**pdata, category_id=cat_map[cat_slug].id)
            db.session.add(product)
            prods_created += 1

    db.session.commit()
    return cats_created, prods_created
