"""Create disposable sample data for the isolated debug launch mode."""

import base64

from src import database as db
from src.crypto import (
    create_verification_hash,
    derive_key,
    generate_salt,
)
from src.history import init_password_history_table

DEBUG_MASTER_PASSWORD = "debug-only"


def create_debug_vault() -> bytes:
    """Populate the already-isolated database and return its encryption key."""
    db.init_database()
    init_password_history_table()

    salt = generate_salt()
    key = derive_key(DEBUG_MASTER_PASSWORD, salt)
    db.save_master_config(
        base64.b64encode(salt).decode("utf-8"),
        create_verification_hash(DEBUG_MASTER_PASSWORD, salt),
    )
    db.set_setting("auto_lock_minutes", "0")
    db.set_setting("default_theme", "dark")

    personal_id = db.add_category("Debug - personnel", "#3b82f6", "flask-conical")
    work_id = db.add_category("Debug - travail", "#a855f7", "laptop")

    accounts = [
        ("Demo faible", "weak@example.invalid", "123456", "https://example.com", "Compte fictif pour tester l'audit.", personal_id, ""),
        ("Demo partagé A", "shared-a@example.invalid", "Debug-Shared-Only-2026!", "https://alpha.example.invalid", "Mot de passe partagé fictif.", work_id, "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"),
        ("Demo partagé B", "shared-b@example.invalid", "Debug-Shared-Only-2026!", "https://beta.example.invalid", "Deuxième compte fictif avec le même mot de passe.", work_id, ""),
        ("Demo sans URL", "no-url@example.invalid", "Debug-Unique-Only-2026!", "", "Compte fictif sans URL.", personal_id, ""),
        ("Demo obsolète", "old@example.invalid", "Debug-Old-Only-2026!", "https://old.example.invalid", "Compte fictif daté pour l'audit.", personal_id, ""),
    ]

    account_ids = []
    for name, login, password, url, notes, category_id, totp_secret in accounts:
        account_ids.append(
            db.add_account(
                name, login, password, url, notes, category_id, key,
                totp_secret=totp_secret,
            )
        )

    conn = db.get_connection()
    try:
        conn.execute(
            "UPDATE accounts SET created_at = datetime('now', '-200 days') WHERE id = ?",
            (account_ids[-1],),
        )
        conn.commit()
    finally:
        conn.close()

    return key
