"""
Modèles de données pour VaultApp.

Ce fichier définit les "formes" des données qu'on manipule :
- Account : un compte (nom, login, mot de passe, URL, notes, catégorie)
- Category : une catégorie (nom, couleur, icône)

C'est comme des formulaires vides qui définissent quelles infos on stocke.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Category:
    """
    Une catégorie pour organiser les comptes.
    
    Exemple : "Réseaux sociaux" avec une icône Lucide et une couleur bleue.
    """
    id: Optional[int] = None       # Identifiant unique (géré par SQLite)
    name: str = ""                  # Nom de la catégorie
    color: str = "#6366f1"          # Couleur en hexadécimal (violet par défaut)
    icon: str = "key-round"
    account_count: int = 0          # Nombre de comptes dans cette catégorie


@dataclass
class Account:
    """
    Un compte avec ses identifiants.
    
    Exemple : Netflix, email@gmail.com, mdp123, https://netflix.com
    """
    id: Optional[int] = None       # Identifiant unique (géré par SQLite)
    name: str = ""                  # Nom du service (ex: "Netflix")
    login: str = ""                 # Identifiant / email
    password: str = ""              # Mot de passe (sera chiffré en base)
    url: str = ""                   # URL du site
    notes: str = ""                 # Notes libres
    category_id: Optional[int] = None  # ID de la catégorie
    category_name: str = ""         # Nom de la catégorie (pour l'affichage)
    category_color: str = "#6366f1" # Couleur de la catégorie (pour l'affichage)
    category_icon: str = "key-round"
    created_at: str = ""            # Date de création
    updated_at: str = ""            # Date de dernière modification
    favorite: bool = False          # Compte épinglé dans les favoris
    totp_secret: str = ""           # Secret TOTP déchiffré en mémoire
    totp_secret_error: bool = False # Indique un secret TOTP illisible en base


# ══════════════════════════════════════════════════════════════
# Bibliothèque d'icônes disponibles pour les catégories
# ══════════════════════════════════════════════════════════════

CATEGORY_ICONS = [
    "smartphone", "message-square", "camera", "bird", "users-round", "mail",
    "inbox", "send",
    "landmark", "credit-card", "wallet-cards", "banknote",
    "chart-no-axes-column-increasing",
    "shopping-cart", "shopping-bag", "store", "gift", "gem",
    "gamepad-2", "target", "trophy", "dice-5",
    "briefcase-business", "building-2", "chart-pie", "clipboard-list",
    "laptop",
    "clapperboard", "music-2", "tv", "headphones", "book-open",
    "plane", "car-front", "hotel", "map", "train-front",
    "hospital", "pill", "stethoscope", "heart", "activity",
    "graduation-cap", "library", "microscope", "flask-conical", "pencil",
    "key-round", "globe", "star", "settings-2", "house",
    "lock-keyhole", "folder", "cloud", "shield", "zap",
]

# ══════════════════════════════════════════════════════════════
# Palette de couleurs pour les catégories
# ══════════════════════════════════════════════════════════════

CATEGORY_COLORS = [
    {"name": "Indigo",    "hex": "#6366f1"},
    {"name": "Bleu",      "hex": "#3b82f6"},
    {"name": "Cyan",      "hex": "#06b6d4"},
    {"name": "Émeraude",  "hex": "#10b981"},
    {"name": "Vert",      "hex": "#22c55e"},
    {"name": "Lime",      "hex": "#84cc16"},
    {"name": "Jaune",     "hex": "#eab308"},
    {"name": "Orange",    "hex": "#f97316"},
    {"name": "Rouge",     "hex": "#ef4444"},
    {"name": "Rose",      "hex": "#ec4899"},
    {"name": "Violet",    "hex": "#a855f7"},
    {"name": "Fuchsia",   "hex": "#d946ef"},
    {"name": "Gris",      "hex": "#6b7280"},
    {"name": "Ardoise",   "hex": "#475569"},
]
