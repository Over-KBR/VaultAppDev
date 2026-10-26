"""
Historique des mots de passe — VaultApp V2.

Stocke les 3 dernières versions du mot de passe pour chaque compte.
Les anciens mots de passe sont conservés chiffrés, accessibles mais masqués.
"""

import sqlite3
from typing import List
from src.database import get_connection
from src.crypto import encrypt, decrypt


def init_password_history_table():
    """Crée la table d'historique si elle n'existe pas."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            password_encrypted TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def push_password_history(account_id: int, old_password: str, encryption_key: bytes):
    """
    Sauvegarde l'ancien mot de passe dans l'historique.
    Garde seulement les 3 dernières versions.
    """
    if not old_password:
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Insérer l'ancienne version
    encrypted = encrypt(old_password, encryption_key)
    cursor.execute(
        "INSERT INTO password_history (account_id, password_encrypted) VALUES (?, ?)",
        (account_id, encrypted),
    )

    # Supprimer les entrées au-delà de 3
    # On utilise id (autoincrement) et non changed_at pour le tri,
    # car SQLite stocke les timestamps à la seconde — plusieurs insertions
    # rapides peuvent avoir le même timestamp et rendre le tri non déterministe.
    cursor.execute("""
        DELETE FROM password_history
        WHERE account_id = ?
          AND id NOT IN (
              SELECT id FROM password_history
              WHERE account_id = ?
              ORDER BY id DESC
              LIMIT 3
          )
    """, (account_id, account_id))

    conn.commit()
    conn.close()


def get_password_history(account_id: int, encryption_key: bytes) -> List[dict]:
    """
    Récupère les 3 derniers mots de passe d'un compte (déchiffrés).

    Returns:
        Liste de dicts {"password": str, "changed_at": str}
        du plus récent au plus ancien.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT password_encrypted, changed_at
        FROM password_history
        WHERE account_id = ?
        ORDER BY id DESC
        LIMIT 3
    """, (account_id,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        try:
            pwd = decrypt(row["password_encrypted"], encryption_key)
        except Exception:
            pwd = "⚠️ Erreur de déchiffrement"
        history.append({"password": pwd, "changed_at": row["changed_at"]})
    return history


def get_all_last_changed_dates() -> dict:
    """
    Récupère la date du dernier changement de mot de passe (MAX(changed_at))
    pour chaque compte présent dans l'historique.

    Returns:
        dict: {account_id: timestamp_str}
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT account_id, MAX(changed_at) as last_changed
        FROM password_history
        GROUP BY account_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return {row["account_id"]: row["last_changed"] for row in rows}
