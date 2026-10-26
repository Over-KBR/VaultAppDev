"""
Export / Import du coffre — VaultApp V2.

Format .vault : fichier JSON chiffré avec AES-256-GCM.
Le JSON contient comptes + catégories.
Chiffré avec la clé dérivée du mot de passe maître (même clé que la DB).
"""

import json
import os
import base64
from src.crypto import encrypt, decrypt, NONCE_SIZE
from src import database as db


def export_vault(path: str, encryption_key: bytes):
    """
    Exporte toutes les données en fichier .vault chiffré.

    Le contenu JSON est chiffré avec AES-256-GCM avant écriture.
    """
    # Récupérer toutes les données
    categories = db.get_all_categories()
    accounts = db.get_all_accounts(encryption_key)

    payload = {
        "version": 2,
        "categories": [
            {"id": c.id, "name": c.name, "color": c.color, "icon": c.icon}
            for c in categories
        ],
        "accounts": [
            {
                "name": a.name,
                "login": a.login,
                "password": a.password,
                "url": a.url,
                "notes": a.notes,
                "totp_secret": a.totp_secret,
                "category_name": a.category_name,
                "favorite": a.favorite,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
            }
            for a in accounts
        ],
    }

    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    # Chiffrer le JSON
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(encryption_key)
    ciphertext = aesgcm.encrypt(nonce, json_bytes, None)

    # Écrire : base64(nonce + ciphertext)
    encoded = base64.b64encode(nonce + ciphertext)
    with open(path, "wb") as f:
        f.write(b"VAULT2\n")  # magic header
        f.write(encoded)


def import_vault(path: str, encryption_key: bytes):
    """
    Importe un fichier .vault et remplace les données actuelles.

    Raises:
        ValueError si le fichier est invalide ou la clé incorrecte.
    """
    with open(path, "rb") as f:
        header = f.readline().strip()
        if header != b"VAULT2":
            raise ValueError("Fichier .vault invalide ou version incompatible.")
        encoded = f.read()

    # Déchiffrer
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    raw = base64.b64decode(encoded)
    nonce = raw[:NONCE_SIZE]
    ciphertext = raw[NONCE_SIZE:]
    aesgcm = AESGCM(encryption_key)

    try:
        json_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        raise ValueError(
            "Impossible de déchiffrer le fichier.\n"
            "Assure-toi d'utiliser le même mot de passe maître."
        )

    payload = json.loads(json_bytes.decode("utf-8"))

    if payload.get("version") != 2:
        raise ValueError("Version de fichier non supportée.")

    # Reconstruire la base (remplacer)
    _restore_data(payload, encryption_key)


def _restore_data(payload: dict, encryption_key: bytes):
    """Vide la base et réimporte les données du payload."""
    import sqlite3
    from src.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Vider les tables dans l'ordre (clés étrangères)
        cursor.execute("DELETE FROM password_history") if _table_exists(cursor, "password_history") else None
        cursor.execute("DELETE FROM accounts")
        cursor.execute("DELETE FROM categories")

        # Recréer les catégories (map name → new_id)
        cat_map = {}
        for cat in payload.get("categories", []):
            cursor.execute(
                "INSERT INTO categories (name, color, icon) VALUES (?, ?, ?)",
                (cat["name"], cat["color"], cat["icon"]),
            )
            cat_map[cat["name"]] = cursor.lastrowid

        # Recréer les comptes
        from src.crypto import encrypt as _enc
        for acc in payload.get("accounts", []):
            cat_id = cat_map.get(acc.get("category_name"))
            cursor.execute("""
                INSERT INTO accounts (name, login, password_encrypted, url,
                                      notes_encrypted, category_id,
                                      created_at, updated_at, favorite,
                                      totp_secret_encrypted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                acc["name"],
                acc.get("login", ""),
                _enc(acc.get("password", ""), encryption_key),
                acc.get("url", ""),
                _enc(acc.get("notes", ""), encryption_key),
                cat_id,
                acc.get("created_at", ""),
                acc.get("updated_at", ""),
                int(bool(acc.get("favorite", False))),
                _enc(acc.get("totp_secret", ""), encryption_key),
            ))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None
