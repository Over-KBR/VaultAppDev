"""
Gestion de la base de données SQLite pour VaultApp.

La base de données est un fichier unique (vault.db) stocké dans :
  %AppData%\\VaultApp\\vault.db

Elle contient 3 tables :
- config : stocke le sel et le hash de vérification du mot de passe maître
- categories : les catégories avec nom, couleur et icône
- accounts : les comptes avec identifiants chiffrés

Tout est dans un seul fichier. Si tu supprimes ce fichier, toutes les données
sont perdues (c'est pour ça qu'on fera un export plus tard en V2).
"""

import os
import sqlite3
from typing import List, Optional, Tuple
from src.models import Account, Category
from src.crypto import encrypt, decrypt


def get_db_path() -> str:
    """
    Retourne le chemin vers la base de données.
    
    La base est dans %AppData%\\VaultApp\\vault.db
    Le dossier est créé automatiquement s'il n'existe pas.
    """
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    vault_dir = os.path.join(appdata, 'VaultApp')
    os.makedirs(vault_dir, exist_ok=True)
    return os.path.join(vault_dir, 'vault.db')


def get_connection() -> sqlite3.Connection:
    """Crée une connexion à la base de données."""
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")  # Mode écriture plus performant
    conn.execute("PRAGMA foreign_keys=ON")    # Active les clés étrangères
    conn.row_factory = sqlite3.Row            # Accès par nom de colonne
    return conn


def init_database():
    """
    Crée les tables si elles n'existent pas.
    Appelé au premier lancement de l'application.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table de configuration (mot de passe maître)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Table des catégories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#6366f1',
            icon TEXT NOT NULL DEFAULT '🔑',
            sort_order INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    # Table des comptes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            login TEXT NOT NULL DEFAULT '',
            password_encrypted TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            notes_encrypted TEXT NOT NULL DEFAULT '',
            category_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════
# Configuration (mot de passe maître)
# ══════════════════════════════════════════════════════════════

def is_first_launch() -> bool:
    """Vérifie si c'est le premier lancement (pas encore de mot de passe maître)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'salt'")
    row = cursor.fetchone()
    conn.close()
    return row is None


def save_master_config(salt_b64: str, verification_hash: str):
    """Sauvegarde le sel et le hash de vérification du mot de passe maître."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('salt', ?)", (salt_b64,))
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('verification_hash', ?)", (verification_hash,))
    conn.commit()
    conn.close()


def get_master_config() -> Tuple[Optional[str], Optional[str]]:
    """Récupère le sel et le hash de vérification."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM config WHERE key = 'salt'")
    salt_row = cursor.fetchone()
    
    cursor.execute("SELECT value FROM config WHERE key = 'verification_hash'")
    hash_row = cursor.fetchone()
    
    conn.close()
    
    salt = salt_row['value'] if salt_row else None
    v_hash = hash_row['value'] if hash_row else None
    
    return salt, v_hash


# ══════════════════════════════════════════════════════════════
# Catégories
# ══════════════════════════════════════════════════════════════

def get_all_categories() -> List[Category]:
    """Récupère toutes les catégories avec le nombre de comptes dans chacune."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(a.id) as account_count
        FROM categories c
        LEFT JOIN accounts a ON a.category_id = c.id
        GROUP BY c.id
        ORDER BY c.sort_order, c.name
    """)
    rows = cursor.fetchall()
    conn.close()
    
    categories = []
    for row in rows:
        categories.append(Category(
            id=row['id'],
            name=row['name'],
            color=row['color'],
            icon=row['icon'],
            account_count=row['account_count'],
        ))
    return categories


def add_category(name: str, color: str, icon: str) -> int:
    """Ajoute une catégorie et retourne son ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO categories (name, color, icon) VALUES (?, ?, ?)",
        (name, color, icon)
    )
    cat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cat_id


def update_category(cat_id: int, name: str, color: str, icon: str):
    """Met à jour une catégorie existante."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE categories SET name = ?, color = ?, icon = ? WHERE id = ?",
        (name, color, icon, cat_id)
    )
    conn.commit()
    conn.close()


def delete_category(cat_id: int):
    """Supprime une catégorie. Les comptes associés deviennent "sans catégorie"."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


def create_default_categories():
    """Crée des catégories par défaut au premier lancement."""
    defaults = [
        ("Réseaux sociaux", "#3b82f6", "📱"),
        ("Email", "#10b981", "📧"),
        ("Banque", "#eab308", "🏦"),
        ("Shopping", "#f97316", "🛒"),
        ("Jeux", "#a855f7", "🎮"),
        ("Travail", "#6b7280", "💼"),
        ("Divertissement", "#ec4899", "🎬"),
    ]
    for name, color, icon in defaults:
        add_category(name, color, icon)


# ══════════════════════════════════════════════════════════════
# Comptes
# ══════════════════════════════════════════════════════════════

def get_all_accounts(encryption_key: bytes, category_id: Optional[int] = None, 
                      search_query: str = "") -> List[Account]:
    """
    Récupère tous les comptes, déchiffrés.
    
    Args:
        encryption_key: La clé AES pour déchiffrer les mots de passe
        category_id: Filtrer par catégorie (None = toutes)
        search_query: Recherche par nom, login ou URL
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT a.*, 
               c.name as cat_name, c.color as cat_color, c.icon as cat_icon
        FROM accounts a
        LEFT JOIN categories c ON a.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if category_id is not None:
        query += " AND a.category_id = ?"
        params.append(category_id)
    
    if search_query:
        query += " AND (a.name LIKE ? OR a.login LIKE ? OR a.url LIKE ?)"
        like = f"%{search_query}%"
        params.extend([like, like, like])
    
    query += " ORDER BY a.name COLLATE NOCASE"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    accounts = []
    for row in rows:
        try:
            decrypted_password = decrypt(row['password_encrypted'], encryption_key)
            decrypted_notes = decrypt(row['notes_encrypted'], encryption_key)
        except Exception:
            decrypted_password = "⚠️ Erreur de déchiffrement"
            decrypted_notes = ""
        
        accounts.append(Account(
            id=row['id'],
            name=row['name'],
            login=row['login'],
            password=decrypted_password,
            url=row['url'],
            notes=decrypted_notes,
            category_id=row['category_id'],
            category_name=row['cat_name'] or "Sans catégorie",
            category_color=row['cat_color'] or "#6b7280",
            category_icon=row['cat_icon'] or "🔑",
            created_at=row['created_at'] or "",
            updated_at=row['updated_at'] or "",
        ))
    return accounts


def add_account(name: str, login: str, password: str, url: str, notes: str,
                category_id: Optional[int], encryption_key: bytes) -> int:
    """Ajoute un compte avec mot de passe chiffré."""
    conn = get_connection()
    cursor = conn.cursor()
    
    encrypted_password = encrypt(password, encryption_key)
    encrypted_notes = encrypt(notes, encryption_key)
    
    cursor.execute("""
        INSERT INTO accounts (name, login, password_encrypted, url, notes_encrypted, category_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, login, encrypted_password, url, encrypted_notes, category_id))
    
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return account_id


def update_account(account_id: int, name: str, login: str, password: str, 
                   url: str, notes: str, category_id: Optional[int], 
                   encryption_key: bytes):
    """Met à jour un compte existant."""
    conn = get_connection()
    cursor = conn.cursor()
    
    encrypted_password = encrypt(password, encryption_key)
    encrypted_notes = encrypt(notes, encryption_key)
    
    cursor.execute("""
        UPDATE accounts 
        SET name = ?, login = ?, password_encrypted = ?, url = ?, 
            notes_encrypted = ?, category_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (name, login, encrypted_password, url, encrypted_notes, category_id, account_id))
    
    conn.commit()
    conn.close()


def delete_account(account_id: int):
    """Supprime un compte."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()


def get_total_account_count() -> int:
    """Retourne le nombre total de comptes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM accounts")
    row = cursor.fetchone()
    conn.close()
    return row['count']


# ══════════════════════════════════════════════════════════════
# Paramètres de l'application (V2)
# ══════════════════════════════════════════════════════════════

def get_setting(key: str, default: str = "") -> str:
    """Récupère un paramètre de configuration."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    """Enregistre un paramètre de configuration."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_all_accounts_raw(category_id=None, search_query=""):
    """
    Retourne les comptes avec mot de passe CHIFFRÉ (pour scan de doublons/faiblesses).
    Usage interne uniquement.
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT a.id, a.name, a.password_encrypted,
               c.name as cat_name, c.color as cat_color, c.icon as cat_icon
        FROM accounts a
        LEFT JOIN categories c ON a.category_id = c.id
        WHERE 1=1
    """
    params = []
    if category_id is not None:
        query += " AND a.category_id = ?"
        params.append(category_id)
    if search_query:
        query += " AND (a.name LIKE ? OR a.login LIKE ?)"
        like = f"%{search_query}%"
        params.extend([like, like])
    query += " ORDER BY a.name COLLATE NOCASE"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def change_master_password(new_password: str, new_salt: bytes, new_hash: str,
                            old_key: bytes, new_key: bytes):
    """
    Change le mot de passe maître et re-chiffre tous les mots de passe.
    Opération atomique : tout passe ou rien.
    """
    from src.crypto import encrypt, decrypt
    import base64

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Re-chiffrer les comptes et l'historique dans la même transaction.
        cursor.execute("SELECT id, password_encrypted, notes_encrypted FROM accounts")
        rows = cursor.fetchall()

        for row in rows:
            pwd_plain = decrypt(row["password_encrypted"], old_key)
            notes_plain = decrypt(row["notes_encrypted"], old_key)
            new_pwd_enc = encrypt(pwd_plain, new_key)
            new_notes_enc = encrypt(notes_plain, new_key)

            cursor.execute(
                "UPDATE accounts SET password_encrypted = ?, notes_encrypted = ? WHERE id = ?",
                (new_pwd_enc, new_notes_enc, row["id"]),
            )

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'password_history'"
        )
        if cursor.fetchone():
            cursor.execute(
                "SELECT id, password_encrypted FROM password_history"
            )
            for row in cursor.fetchall():
                password = decrypt(row["password_encrypted"], old_key)
                cursor.execute(
                    "UPDATE password_history SET password_encrypted = ? WHERE id = ?",
                    (encrypt(password, new_key), row["id"]),
                )

        salt_b64 = base64.b64encode(new_salt).decode("utf-8")
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('salt', ?)", (salt_b64,))
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('verification_hash', ?)",
            (new_hash,),
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
