"""
Fixtures partagées pour les tests VaultApp.

conftest.py est chargé automatiquement par pytest.
Les fixtures définies ici sont disponibles dans tous les fichiers de tests.
"""

import os
import sys
import pytest
import tempfile

# Ajouter la racine du projet au path pour que les imports src.* fonctionnent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Fixtures crypto ──────────────────────────────────────────

@pytest.fixture
def master_password():
    """Mot de passe maître de test."""
    return "TestMasterPassword42!"


@pytest.fixture
def salt(master_password):
    """Sel aléatoire dérivé pour les tests."""
    from src.crypto import generate_salt
    return generate_salt()


@pytest.fixture
def encryption_key(master_password, salt):
    """Clé AES-256 dérivée du mot de passe maître."""
    from src.crypto import derive_key
    return derive_key(master_password, salt)


# ── Fixtures base de données ─────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """
    Base de données SQLite temporaire isolée pour chaque test.

    Utilise monkeypatch pour rediriger get_db_path() vers un fichier
    temporaire, de sorte que les tests ne touchent jamais la vraie DB
    de l'utilisateur dans %AppData%.
    """
    db_file = str(tmp_path / "vault_test.db")

    import src.database as db_module
    monkeypatch.setattr(db_module, "get_db_path", lambda: db_file)

    # Initialiser les tables
    from src.database import init_database
    init_database()

    # Initialiser la table historique
    from src.history import init_password_history_table
    init_password_history_table()

    yield db_file


@pytest.fixture
def db_with_data(tmp_db, encryption_key):
    """
    Base de données pré-remplie avec des catégories et comptes de test.
    Retourne l'encryption_key pour les opérations de déchiffrement.
    """
    from src.database import add_category, add_account

    # Catégories
    cat1_id = add_category("Réseaux sociaux", "#3b82f6", "📱")
    cat2_id = add_category("Banque", "#eab308", "🏦")

    # Comptes
    add_account("Twitter", "user@test.com", "weak", "https://twitter.com",
                "note test", cat1_id, encryption_key)
    add_account("GitHub", "dev@test.com", "Tr0ub4dor&3_SecurePass!", "https://github.com",
                "", cat1_id, encryption_key)
    add_account("BNP", "user@test.com", "Tr0ub4dor&3_SecurePass!", "https://bnp.fr",
                "", cat2_id, encryption_key)  # même mdp que GitHub = doublon

    return encryption_key
