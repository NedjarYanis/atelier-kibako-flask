"""
Définition des 5 univers de boutiques inspirés des 5 sites de référence :
1. roche-bobois  (Roche Bobois — Luxe architectural & French Art de Vivre)
2. popchart      (Pop Chart — Blueprint infographique & taxonomie technique)
3. fromourplace  (Our Place — D2C chaleureux, terracotta & pastels arrondis)
4. fishwife      (Fishwife — Néo-vintage pop, bordures franches & couleurs vives)
5. lepetitsouk   (Le Petit Souk — Concept-store poétique, doux & pétillant)
"""

SITES = {
    "roche-bobois": {
        "slug": "roche-bobois",
        "brand_name": "KIBAKO MAISON",
        "subtitle": "Haute Ébénisterie Musicale · Inspiration Roche Bobois",
        "inspiration_url": "roche-bobois.com",
        "tagline": "Le design sonore et le French Art de Vivre.",
        "hero_kicker": "COLLECTION AUTOMNE-HIVER · PIÈCES SIGNÉES",
        "hero_title": "L'architecture du bois et du laiton, accordée à la main.",
        "hero_desc": (
            "Des boîtes à musique sculpturales façonnées en essences nobles, "
            "pensées comme des objets de collection pour votre intérieur."
        ),
        "cta_primary": "Découvrir les créations",
        "cta_secondary": "Studio 3D sur-mesure",
        "badge_label": "Prix Découverte",
        "style_notes": "Galerie épurée, typographie haute couture, accents or champagne, espace négatif.",
        "colors": ["#FFFFFF", "#111111", "#C5A059", "#F4F2EE"],
        "cad_bg": "#141414",
        "cad_accent": "#C5A059",
    },
    "popchart": {
        "slug": "popchart",
        "brand_name": "KIBAKO CHART",
        "subtitle": "Nomenclature Acoustique · Inspiration Pop Chart",
        "inspiration_url": "popchart.co",
        "tagline": "The Melodies You Love. Engineered.",
        "hero_kicker": "ARCHIVE ACOUSTIQUE · SÉRIE SCHÉMATIQUE",
        "hero_title": "Chaque note cartographiée, chaque lame calibrée.",
        "hero_desc": (
            "Une approche encyclopédique de la boîte à musique : fréquences en Hz, "
            "plans de coupe, essences répertoriées et cylindres de précision."
        ),
        "cta_primary": "Explorer l'index",
        "cta_secondary": "Inspecteur Blueprint",
        "badge_label": "SPEC 18/30 LAMES",
        "style_notes": "Grille blueprint, papier archive crème, bleu technique #1B365D, monospace.",
        "colors": ["#F7F4EB", "#1B365D", "#D94E34", "#2B2B2B"],
        "cad_bg": "#132642",
        "cad_accent": "#E8B84B",
    },
    "fromourplace": {
        "slug": "fromourplace",
        "brand_name": "NOTRE KIBAKO",
        "subtitle": "Objets du Quotidien · Inspiration Our Place",
        "inspiration_url": "fromourplace.fr",
        "tagline": "Pensées pour rassembler, faites pour durer.",
        "hero_kicker": "ESSAI 100 JOURS · LIVRAISON OFFERTE DÈS 80 €",
        "hero_title": "La boîte à musique réinventée pour votre table de chevet.",
        "hero_desc": (
            "Des lignes douces, des bois sourcés sans traitement toxique et des teintes "
            "naturelles qui réchauffent instantanément chaque pièce de la maison."
        ),
        "cta_primary": "Voir nos best-sellers",
        "cta_secondary": "Configurer en 3D",
        "badge_label": "Édition Atelier",
        "style_notes": "Terre cuite #C85A32, crème doux #FDF8F3, cartes arrondies, pastilles d'essences.",
        "colors": ["#FDF8F3", "#C85A32", "#7E8D74", "#3D312A"],
        "cad_bg": "#2A211C",
        "cad_accent": "#C85A32",
    },
    "fishwife": {
        "slug": "fishwife",
        "brand_name": "KIBAKO CONSERVE",
        "subtitle": "Éditions Collector Pop · Inspiration Fishwife",
        "inspiration_url": "eatfishwife.com",
        "tagline": "Des mélodies cultes, mises en boîte avec panache.",
        "hero_kicker": "ÉDITION LIMITÉE · COLLECTOR POP CULTURE",
        "hero_title": "Ouvrez le couvercle. Libérez le son.",
        "hero_desc": (
            "Des coffrets en bois au caractère bien trempé, gravés comme des pièces "
            "de collection néo-rétro pour les fans de manga, cinéma et jeux vidéo."
        ),
        "cta_primary": "Attraper une boîte !",
        "cta_secondary": "Mode Éclaté 3D",
        "badge_label": "BEST-SELLER!",
        "style_notes": "Jaune soleil #F7D147, rouge corail #E84A3C, bordures noires 2.5px & ombres dures.",
        "colors": ["#FFF9EC", "#F7D147", "#E84A3C", "#1D4ED8"],
        "cad_bg": "#191919",
        "cad_accent": "#F7D147",
    },
    "lepetitsouk": {
        "slug": "lepetitsouk",
        "brand_name": "LE PETIT KIBAKO",
        "subtitle": "Concept-Store Poétique · Inspiration Le Petit Souk",
        "inspiration_url": "lepetitsouk.fr",
        "tagline": "Petits trésors en bois & grandes émotions musicales.",
        "hero_kicker": "IDÉES CADEAUX · UNIVERS PÉTILLANT",
        "hero_title": "Des boîtes à musique comme des souvenirs d'enfance.",
        "hero_desc": (
            "Un bazar chic rempli de douceur, de bois dorés, de mélodies Ghibli "
            "et de coffrets prêts à offrir pour émerveiller petits et grands."
        ),
        "cta_primary": "Chiner les merveilles",
        "cta_secondary": "Écouter une berceuse",
        "badge_label": "Coup de cœur ♥",
        "style_notes": "Rose poudré #F9D5D3, menthe #CDE8E0, moutarde #F4C95D, esprit concept-store.",
        "colors": ["#FFFDFB", "#F9D5D3", "#CDE8E0", "#D96B43"],
        "cad_bg": "#262024",
        "cad_accent": "#F4C95D",
    },
}

SITES_ORDER = ["roche-bobois", "popchart", "fromourplace", "fishwife", "lepetitsouk"]
