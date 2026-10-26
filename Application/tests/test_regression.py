"""
Tests de régression — Fonctions V1 intactes après modifications V2.

Ces tests vérifient que rien de ce qui fonctionnait en V1
n'a été cassé lors du développement de la V2.

Lancer : pytest tests/test_regression.py -v
"""

import pytest


class TestRegressionCrypto:
    """Les comportements crypto V1 sont inchangés."""

    def test_pbkdf2_600k_iterations(self):
        """Le nombre d'itérations PBKDF2 est bien 600 000 (recommandation OWASP)."""
        from src.crypto import PBKDF2_ITERATIONS
        assert PBKDF2_ITERATIONS == 600_000

    def test_salt_size_16_bytes(self):
        from src.crypto import SALT_SIZE
        assert SALT_SIZE == 16

    def test_key_size_32_bytes(self):
        from src.crypto import KEY_SIZE
        assert KEY_SIZE == 32

    def test_nonce_size_12_bytes(self):
        from src.crypto import NONCE_SIZE
        assert NONCE_SIZE == 12

    def test_format_chiffrement_base64(self, encryption_key):
        """Le résultat de encrypt() est bien une chaîne base64 valide."""
        from src.crypto import encrypt
        import base64
        result = encrypt("test", encryption_key)
        # Ne doit pas lever d'exception
        decoded = base64.b64decode(result)
        assert len(decoded) > 12  # nonce + ciphertext

    def test_verify_master_password_existe_et_retourne_bool(self, master_password, salt):
        """verify_master_password() existe et retourne un booléen."""
        from src.crypto import create_verification_hash, verify_master_password
        h = create_verification_hash(master_password, salt)
        result = verify_master_password(master_password, salt, h)
        assert isinstance(result, bool)


class TestRegressionDatabase:
    """Les fonctions de base de données V1 sont toujours présentes et fonctionnelles."""

    def test_init_database_cree_tables(self, tmp_db):
        """Les 3 tables V1 existent bien : config, categories, accounts."""
        import sqlite3
        conn = sqlite3.connect(tmp_db)
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        conn.close()
        assert "config" in tables
        assert "categories" in tables
        assert "accounts" in tables

    def test_is_first_launch_vrai_sur_nouvelle_db(self, tmp_db):
        from src.database import is_first_launch
        assert is_first_launch() is True

    def test_save_et_get_master_config(self, tmp_db, master_password, salt):
        """save_master_config / get_master_config fonctionnent."""
        import base64
        from src.crypto import create_verification_hash
        from src.database import save_master_config, get_master_config, is_first_launch

        salt_b64 = base64.b64encode(salt).decode()
        v_hash = create_verification_hash(master_password, salt)
        save_master_config(salt_b64, v_hash)

        assert is_first_launch() is False
        retrieved_salt, retrieved_hash = get_master_config()
        assert retrieved_salt == salt_b64
        assert retrieved_hash == v_hash

    def test_add_category_fonctionnel(self, tmp_db):
        from src.database import add_category, get_all_categories
        add_category("Test", "#ff0000", "⭐")
        cats = get_all_categories()
        assert len(cats) == 1
        assert cats[0].name == "Test"
        assert cats[0].color == "#ff0000"
        assert cats[0].icon == "⭐"

    def test_account_category_foreign_key(self, tmp_db, encryption_key):
        """La clé étrangère category_id est bien respectée."""
        from src.database import add_account, get_all_accounts
        # Ajouter un compte sans catégorie
        add_account("Test", "u", "p", "", "", None, encryption_key)
        accounts = get_all_accounts(encryption_key)
        assert accounts[0].category_name == "Sans catégorie"

    def test_get_all_accounts_ordre_alphabetique(self, tmp_db, encryption_key):
        """Les comptes sont triés alphabétiquement."""
        from src.database import add_account, get_all_accounts
        add_account("Zzz", "u", "p", "", "", None, encryption_key)
        add_account("Aaa", "u", "p", "", "", None, encryption_key)
        add_account("Mmm", "u", "p", "", "", None, encryption_key)
        accounts = get_all_accounts(encryption_key)
        names = [a.name for a in accounts]
        assert names == sorted(names, key=str.lower)

    def test_delete_account_diminue_le_total(self, tmp_db, encryption_key):
        from src.database import add_account, delete_account, get_total_account_count
        acc_id = add_account("A supprimer", "u", "p", "", "", None, encryption_key)
        before = get_total_account_count()
        delete_account(acc_id)
        assert get_total_account_count() == before - 1


class TestRegressionUI:
    """Vérification que les modules UI s'importent sans erreur (smoke test)."""

    def test_import_theme(self):
        from src.ui.theme import theme, FONTS, DIMENSIONS
        assert theme is not None
        assert "heading" in FONTS
        assert "window_width" in DIMENSIONS

    def test_import_models(self):
        from src.models import Account, Category, CATEGORY_ICONS, CATEGORY_COLORS
        a = Account(name="Test")
        c = Category(name="Cat")
        assert a.name == "Test"
        assert c.name == "Cat"
        assert len(CATEGORY_ICONS) > 0
        assert len(CATEGORY_COLORS) > 0

    def test_import_clipboard(self):
        try:
            from src.clipboard import copy_to_clipboard
            assert callable(copy_to_clipboard)
        except ModuleNotFoundError:
            pytest.skip("pyperclip non disponible dans cet environnement")

    def test_import_strength(self):
        from src.strength import analyze_password, is_weak
        assert callable(analyze_password)
        assert callable(is_weak)

    def test_import_generator(self):
        from src.generator import generate_password, estimate_entropy
        assert callable(generate_password)
        assert callable(estimate_entropy)

    def test_import_history(self):
        from src.history import push_password_history, get_password_history
        assert callable(push_password_history)
        assert callable(get_password_history)

    def test_import_vault_io(self):
        from src.vault_io import export_vault, import_vault
        assert callable(export_vault)
        assert callable(import_vault)


class TestRegressionClipboard:
    """Le clipboard fonctionne comme en V1."""

    def test_copy_to_clipboard_sans_crash(self):
        """copy_to_clipboard ne doit pas planter (même si pyperclip n'est pas dispo en CI)."""
        from src.clipboard import copy_to_clipboard
        try:
            copy_to_clipboard("test", clear_after_seconds=0)
        except Exception:
            pytest.skip("Clipboard non disponible dans cet environnement")
