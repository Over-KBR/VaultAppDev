"""
Tests d'intégration — Base de données, CRUD, historique, export/import.

Ces tests vérifient que les composants fonctionnent ensemble
sur une base de données temporaire isolée.

Lancer : pytest tests/test_integration.py -v
"""

import pytest
import os


# ══════════════════════════════════════════════════════════════
# CRUD CATÉGORIES
# ══════════════════════════════════════════════════════════════

class TestCategories:
    """Tests CRUD sur les catégories."""

    def test_ajouter_categorie(self, tmp_db):
        from src.database import add_category, get_all_categories
        add_category("Jeux", "#a855f7", "🎮")
        cats = get_all_categories()
        assert any(c.name == "Jeux" for c in cats)

    def test_categorie_retourne_id(self, tmp_db):
        from src.database import add_category
        cat_id = add_category("Test", "#ff0000", "⭐")
        assert isinstance(cat_id, int)
        assert cat_id > 0

    def test_modifier_categorie(self, tmp_db):
        from src.database import add_category, update_category, get_all_categories
        cat_id = add_category("Ancien nom", "#ff0000", "⭐")
        update_category(cat_id, "Nouveau nom", "#00ff00", "🌟")
        cats = get_all_categories()
        cat = next(c for c in cats if c.id == cat_id)
        assert cat.name == "Nouveau nom"
        assert cat.color == "#00ff00"
        assert cat.icon == "🌟"

    def test_supprimer_categorie(self, tmp_db):
        from src.database import add_category, delete_category, get_all_categories
        cat_id = add_category("A supprimer", "#ff0000", "🗑️")
        delete_category(cat_id)
        cats = get_all_categories()
        assert all(c.id != cat_id for c in cats)

    def test_categories_par_defaut(self, tmp_db):
        from src.database import create_default_categories, get_all_categories
        create_default_categories()
        cats = get_all_categories()
        assert len(cats) == 7

    def test_supprimer_categorie_met_comptes_sans_categorie(self, tmp_db, encryption_key):
        """Supprimer une catégorie ne supprime pas les comptes associés."""
        from src.database import add_category, delete_category, add_account, get_all_accounts
        cat_id = add_category("Temp", "#ff0000", "🔥")
        add_account("Compte test", "user", "pass123", "", "", cat_id, encryption_key)
        delete_category(cat_id)
        accounts = get_all_accounts(encryption_key)
        assert any(a.name == "Compte test" for a in accounts)
        # Le compte doit être sans catégorie
        acc = next(a for a in accounts if a.name == "Compte test")
        assert acc.category_id is None


# ══════════════════════════════════════════════════════════════
# CRUD COMPTES
# ══════════════════════════════════════════════════════════════

class TestAccounts:
    """Tests CRUD sur les comptes."""

    def test_ajouter_compte(self, tmp_db, encryption_key):
        from src.database import add_account, get_all_accounts
        add_account("Netflix", "user@test.com", "MonMdp123!", "https://netflix.com",
                    "Notes ici", None, encryption_key)
        accounts = get_all_accounts(encryption_key)
        assert any(a.name == "Netflix" for a in accounts)

    def test_compte_retourne_id(self, tmp_db, encryption_key):
        from src.database import add_account
        acc_id = add_account("Test", "u", "p", "", "", None, encryption_key)
        assert isinstance(acc_id, int)
        assert acc_id > 0

    def test_mot_de_passe_chiffre_en_base(self, tmp_db, encryption_key):
        """Le mot de passe est stocké chiffré, pas en clair."""
        from src.database import add_account
        import sqlite3
        acc_id = add_account("Test", "u", "SecretClair", "", "", None, encryption_key)
        conn = sqlite3.connect(tmp_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT password_encrypted FROM accounts WHERE id=?", (acc_id,)).fetchone()
        conn.close()
        assert row["password_encrypted"] != "SecretClair"

    def test_lire_compte_dechiffre(self, tmp_db, encryption_key):
        """get_all_accounts() retourne le mot de passe déchiffré."""
        from src.database import add_account, get_all_accounts
        add_account("Steam", "gamer@test.com", "GamePass#99", "https://store.steampowered.com",
                    "", None, encryption_key)
        accounts = get_all_accounts(encryption_key)
        steam = next(a for a in accounts if a.name == "Steam")
        assert steam.password == "GamePass#99"
        assert steam.login == "gamer@test.com"

    def test_modifier_compte(self, tmp_db, encryption_key):
        from src.database import add_account, update_account, get_all_accounts
        acc_id = add_account("Spotify", "old@test.com", "oldpass", "", "", None, encryption_key)
        update_account(acc_id, "Spotify Premium", "new@test.com", "NewPass#2024!",
                       "https://spotify.com", "abonnement famille", None, encryption_key)
        accounts = get_all_accounts(encryption_key)
        acc = next(a for a in accounts if a.id == acc_id)
        assert acc.name == "Spotify Premium"
        assert acc.login == "new@test.com"
        assert acc.password == "NewPass#2024!"

    def test_supprimer_compte(self, tmp_db, encryption_key):
        from src.database import add_account, delete_account, get_all_accounts
        acc_id = add_account("A supprimer", "u", "p", "", "", None, encryption_key)
        delete_account(acc_id)
        accounts = get_all_accounts(encryption_key)
        assert all(a.id != acc_id for a in accounts)

    def test_filtrer_par_categorie(self, tmp_db, db_with_data):
        from src.database import get_all_accounts, get_all_categories
        cats = get_all_categories()
        banque = next(c for c in cats if c.name == "Banque")
        accounts = get_all_accounts(db_with_data, category_id=banque.id)
        assert len(accounts) == 1
        assert accounts[0].name == "BNP"

    def test_recherche_par_nom(self, tmp_db, db_with_data):
        from src.database import get_all_accounts
        results = get_all_accounts(db_with_data, search_query="git")
        assert len(results) == 1
        assert results[0].name == "GitHub"

    def test_recherche_par_login(self, tmp_db, db_with_data):
        from src.database import get_all_accounts
        results = get_all_accounts(db_with_data, search_query="dev@test")
        assert any(a.name == "GitHub" for a in results)

    def test_recherche_vide_retourne_tout(self, tmp_db, db_with_data):
        from src.database import get_all_accounts, get_total_account_count
        results = get_all_accounts(db_with_data)
        assert len(results) == get_total_account_count()

    def test_compte_total(self, tmp_db, encryption_key):
        from src.database import add_account, get_total_account_count
        before = get_total_account_count()
        add_account("A", "b", "c", "", "", None, encryption_key)
        add_account("D", "e", "f", "", "", None, encryption_key)
        assert get_total_account_count() == before + 2

    def test_notes_chiffrees(self, tmp_db, encryption_key):
        """Les notes sont aussi chiffrées et déchiffrées correctement."""
        from src.database import add_account, get_all_accounts
        add_account("Test notes", "u", "p", "", "Notes confidentielles 🔒", None, encryption_key)
        accounts = get_all_accounts(encryption_key)
        acc = next(a for a in accounts if a.name == "Test notes")
        assert acc.notes == "Notes confidentielles 🔒"

    def test_updated_at_change_lors_modification(self, tmp_db, encryption_key):
        """updated_at doit changer après une modification."""
        import time
        from src.database import add_account, update_account, get_all_accounts
        acc_id = add_account("Test", "u", "p", "", "", None, encryption_key)
        before = next(a for a in get_all_accounts(encryption_key) if a.id == acc_id).updated_at
        time.sleep(1.1)
        update_account(acc_id, "Test", "u", "new_pass", "", "", None, encryption_key)
        after = next(a for a in get_all_accounts(encryption_key) if a.id == acc_id).updated_at
        assert before != after


# ══════════════════════════════════════════════════════════════
# HISTORIQUE
# ══════════════════════════════════════════════════════════════

class TestHistory:
    """Tests sur le module src/history.py."""

    def test_push_et_get(self, tmp_db, encryption_key):
        from src.database import add_account
        from src.history import push_password_history, get_password_history
        acc_id = add_account("Test", "u", "v1_password", "", "", None, encryption_key)
        push_password_history(acc_id, "v1_password", encryption_key)
        history = get_password_history(acc_id, encryption_key)
        assert len(history) == 1
        assert history[0]["password"] == "v1_password"

    def test_limite_3_entrees(self, tmp_db, encryption_key):
        """L'historique ne conserve que les 3 dernières versions."""
        from src.database import add_account
        from src.history import push_password_history, get_password_history
        acc_id = add_account("Test", "u", "init", "", "", None, encryption_key)
        for i in range(1, 5):
            push_password_history(acc_id, f"v{i}_password", encryption_key)
        history = get_password_history(acc_id, encryption_key)
        assert len(history) == 3
        passwords = [h["password"] for h in history]
        # v1 doit avoir été supprimé, les 3 dernières (v2, v3, v4) conservées
        assert "v1_password" not in passwords
        assert "v4_password" in passwords
        assert "v3_password" in passwords
        assert "v2_password" in passwords

    def test_historique_vide_si_aucune_entree(self, tmp_db, encryption_key):
        from src.database import add_account
        from src.history import get_password_history
        acc_id = add_account("Test", "u", "p", "", "", None, encryption_key)
        assert get_password_history(acc_id, encryption_key) == []

    def test_ordre_du_plus_recent_au_plus_ancien(self, tmp_db, encryption_key):
        """L'historique est trié du plus récent au plus ancien."""
        import time
        from src.database import add_account
        from src.history import push_password_history, get_password_history
        acc_id = add_account("Test", "u", "init", "", "", None, encryption_key)
        push_password_history(acc_id, "ancien", encryption_key)
        time.sleep(1.1)
        push_password_history(acc_id, "recent", encryption_key)
        history = get_password_history(acc_id, encryption_key)
        assert history[0]["password"] == "recent"
        assert history[1]["password"] == "ancien"

    def test_historique_supprime_avec_compte(self, tmp_db, encryption_key):
        """Supprimer un compte supprime aussi son historique (ON DELETE CASCADE)."""
        import sqlite3
        from src.database import add_account, delete_account
        from src.history import push_password_history
        acc_id = add_account("Test", "u", "p", "", "", None, encryption_key)
        push_password_history(acc_id, "p", encryption_key)
        delete_account(acc_id)
        conn = sqlite3.connect(tmp_db)
        row = conn.execute("SELECT COUNT(*) FROM password_history WHERE account_id=?", (acc_id,)).fetchone()
        conn.close()
        assert row[0] == 0


# ══════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════

class TestSettings:
    """Tests sur get_setting / set_setting."""

    def test_get_valeur_par_defaut(self, tmp_db):
        from src.database import get_setting
        assert get_setting("inexistant", "default_val") == "default_val"

    def test_set_et_get(self, tmp_db):
        from src.database import get_setting, set_setting
        set_setting("auto_lock_minutes", "5")
        assert get_setting("auto_lock_minutes") == "5"

    def test_set_ecrase_valeur_existante(self, tmp_db):
        from src.database import get_setting, set_setting
        set_setting("theme", "dark")
        set_setting("theme", "light")
        assert get_setting("theme") == "light"


# ══════════════════════════════════════════════════════════════
# EXPORT / IMPORT VAULT
# ══════════════════════════════════════════════════════════════

class TestVaultIO:
    """Tests sur le module src/vault_io.py."""

    def test_export_cree_fichier(self, tmp_db, db_with_data, tmp_path):
        from src.vault_io import export_vault
        path = str(tmp_path / "backup.vault")
        export_vault(path, db_with_data)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_export_header_vault2(self, tmp_db, db_with_data, tmp_path):
        """Le fichier exporté commence bien par le magic header VAULT2."""
        from src.vault_io import export_vault
        path = str(tmp_path / "backup.vault")
        export_vault(path, db_with_data)
        with open(path, "rb") as f:
            header = f.readline().strip()
        assert header == b"VAULT2"

    def test_export_import_roundtrip(self, tmp_db, db_with_data, tmp_path):
        """Exporter puis importer redonne les mêmes données."""
        from src.database import get_all_accounts, get_total_account_count
        from src.vault_io import export_vault, import_vault

        # Compter avant
        count_before = get_total_account_count()
        accounts_before = {a.name for a in get_all_accounts(db_with_data)}

        # Exporter
        path = str(tmp_path / "backup.vault")
        export_vault(path, db_with_data)

        # Vider la base et importer
        import sqlite3
        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM accounts")
        conn.execute("DELETE FROM categories")
        conn.commit()
        conn.close()

        import_vault(path, db_with_data)

        # Vérifier
        accounts_after = {a.name for a in get_all_accounts(db_with_data)}
        assert get_total_account_count() == count_before
        assert accounts_before == accounts_after

    def test_import_mauvaise_cle_leve_valueerror(self, tmp_db, db_with_data, tmp_path, encryption_key):
        """Importer avec une mauvaise clé lève une ValueError."""
        from src.vault_io import export_vault, import_vault
        from src.crypto import derive_key, generate_salt

        path = str(tmp_path / "backup.vault")
        export_vault(path, db_with_data)

        mauvaise_cle = derive_key("MauvaisMotDePasse", generate_salt())
        with pytest.raises(ValueError):
            import_vault(path, mauvaise_cle)

    def test_import_fichier_invalide_leve_valueerror(self, tmp_db, db_with_data, tmp_path):
        """Importer un fichier corrompu lève une ValueError."""
        from src.vault_io import import_vault

        path = str(tmp_path / "corrupt.vault")
        with open(path, "wb") as f:
            f.write(b"BADVAULT\ngarbage_data_here")

        with pytest.raises(ValueError):
            import_vault(path, db_with_data)

    def test_mots_de_passe_restent_lisibles_apres_import(self, tmp_db, db_with_data, tmp_path):
        """Après import, les mots de passe sont correctement déchiffrés."""
        from src.database import get_all_accounts
        from src.vault_io import export_vault, import_vault
        import sqlite3

        # Sauvegarder les mots de passe originaux
        original = {a.name: a.password for a in get_all_accounts(db_with_data)}

        path = str(tmp_path / "backup.vault")
        export_vault(path, db_with_data)

        # Vider et réimporter
        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM accounts")
        conn.execute("DELETE FROM categories")
        conn.commit()
        conn.close()

        import_vault(path, db_with_data)

        restored = {a.name: a.password for a in get_all_accounts(db_with_data)}
        assert original == restored
