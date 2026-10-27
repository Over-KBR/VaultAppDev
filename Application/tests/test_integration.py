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

    def test_favori_persiste_et_se_lit(self, tmp_db, encryption_key):
        from src.database import add_account, get_all_accounts, set_account_favorite

        account_id = add_account("Favori", "login", "secret", "", "", None, encryption_key)
        set_account_favorite(account_id, True)

        account = get_all_accounts(encryption_key)[0]
        assert account.id == account_id
        assert account.favorite is True

    def test_filtrer_favoris_sans_retourner_les_autres_comptes(
        self, tmp_db, encryption_key
    ):
        from src.database import (
            add_account,
            get_all_accounts,
            get_account_stats,
            get_favorite_count,
            set_account_favorite,
        )

        favorite_id = add_account(
            "Favori", "login", "favorite-secret", "", "", None, encryption_key
        )
        add_account("Autre", "login", "other-secret", "", "", None, encryption_key)
        set_account_favorite(favorite_id, True)

        accounts = get_all_accounts(encryption_key, favorite_only=True)
        assert [account.id for account in accounts] == [favorite_id]
        assert get_favorite_count() == 1
        assert get_account_stats() == (2, 1)

    def test_lire_uniquement_les_identifiants_d_un_compte(
        self, tmp_db, encryption_key
    ):
        from src.database import add_account, get_account_credentials_by_id

        account_id = add_account(
            "Exemple", "login@example.invalid", "secret", "", "private note",
            None, encryption_key, totp_secret="private totp",
        )

        account = get_account_credentials_by_id(account_id, encryption_key)
        assert account is not None
        assert account.login == "login@example.invalid"
        assert account.password == "secret"
        assert account.notes == ""
        assert account.totp_secret == ""

    def test_secret_totp_est_chiffre_et_dechiffre(self, tmp_db, encryption_key):
        import sqlite3
        from src.database import add_account, get_all_accounts, update_account

        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        account_id = add_account(
            "TOTP", "login", "password", "", "", None, encryption_key,
            totp_secret=secret,
        )
        with sqlite3.connect(tmp_db) as conn:
            encrypted = conn.execute(
                "SELECT totp_secret_encrypted FROM accounts WHERE id = ?",
                (account_id,),
            ).fetchone()[0]

        account = get_all_accounts(encryption_key)[0]
        assert encrypted != secret
        assert account.totp_secret == secret

        update_account(
            account_id, "TOTP modifié", "login", "password", "", "", None,
            encryption_key,
        )
        account = get_all_accounts(encryption_key)[0]
        assert account.totp_secret == secret

    def test_secret_totp_corrompu_est_signale_sans_cacher_le_compte(
        self, tmp_db, encryption_key
    ):
        from src.database import add_account, get_all_accounts, get_connection

        account_id = add_account(
            "TOTP corrompu", "login", "password", "", "", None, encryption_key,
            totp_secret="GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
        )
        conn = get_connection()
        conn.execute(
            "UPDATE accounts SET totp_secret_encrypted = ? WHERE id = ?",
            ("invalid", account_id),
        )
        conn.commit()
        conn.close()

        account = get_all_accounts(encryption_key)[0]
        assert account.password == "password"
        assert account.totp_secret == ""
        assert account.totp_secret_error is True

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

    def test_ordre_deterministe_si_timestamps_identiques(self, tmp_db, encryption_key):
        import sqlite3
        from src.database import add_account
        from src.history import get_password_history, push_password_history

        account_id = add_account("Test", "u", "init", "", "", None, encryption_key)
        for password in ("premier", "deuxieme", "troisieme"):
            push_password_history(account_id, password, encryption_key)

        conn = sqlite3.connect(tmp_db)
        conn.execute(
            "UPDATE password_history SET changed_at = '2025-01-01 00:00:00' WHERE account_id = ?",
            (account_id,),
        )
        conn.commit()
        conn.close()

        history = get_password_history(account_id, encryption_key)
        assert [entry["password"] for entry in history] == [
            "troisieme", "deuxieme", "premier"
        ]

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

    def test_delai_presse_papiers_configurable(self, tmp_db):
        from src.clipboard import get_clipboard_clear_seconds
        from src.database import set_setting

        assert get_clipboard_clear_seconds() == 30
        set_setting("clipboard_clear_seconds", "15")
        assert get_clipboard_clear_seconds() == 15

    def test_delai_presse_papiers_invalide_signale(self, tmp_db):
        from src.clipboard import get_clipboard_clear_seconds
        from src.database import set_setting

        set_setting("clipboard_clear_seconds", "0")
        with pytest.raises(ValueError):
            get_clipboard_clear_seconds()


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

    def test_export_import_conserve_les_favoris(self, tmp_db, db_with_data, tmp_path):
        from src.database import get_all_accounts, set_account_favorite
        from src.vault_io import export_vault, import_vault

        account = get_all_accounts(db_with_data)[0]
        set_account_favorite(account.id, True)
        path = str(tmp_path / "favorites.vault")
        export_vault(path, db_with_data)

        import_vault(path, db_with_data)

        restored = next(a for a in get_all_accounts(db_with_data) if a.name == account.name)
        assert restored.favorite is True

    def test_export_import_conserve_le_secret_totp(
        self, tmp_db, encryption_key, tmp_path
    ):
        from src.database import add_account, get_all_accounts
        from src.vault_io import export_vault, import_vault

        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        add_account(
            "TOTP", "login", "password", "", "", None, encryption_key,
            totp_secret=secret,
        )
        path = str(tmp_path / "totp.vault")
        export_vault(path, encryption_key)
        import_vault(path, encryption_key)

        assert get_all_accounts(encryption_key)[0].totp_secret == secret

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


class TestMasterPasswordChange:
    def test_change_rechiffre_comptes_et_historique(
        self, tmp_db, master_password, salt, encryption_key
    ):
        import base64
        from src.crypto import create_verification_hash, derive_key, generate_salt
        from src.database import (
            add_account,
            change_master_password,
            get_all_accounts,
            get_master_config,
            save_master_config,
        )
        from src.history import get_password_history, push_password_history

        save_master_config(
            base64.b64encode(salt).decode("utf-8"),
            create_verification_hash(master_password, salt),
        )
        account_id = add_account(
            "Compte de test", "demo@example.invalid", "AncienSecret!",
            "", "Note privée", None, encryption_key,
            totp_secret="GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
        )
        push_password_history(account_id, "AncienSecret!", encryption_key)

        new_password = "NewDebugMaster42!"
        new_salt = generate_salt()
        new_key = derive_key(new_password, new_salt)
        new_hash = create_verification_hash(new_password, new_salt)
        change_master_password(
            new_password, new_salt, new_hash, encryption_key, new_key
        )

        account = get_all_accounts(new_key)[0]
        assert account.password == "AncienSecret!"
        assert account.notes == "Note privée"
        assert account.totp_secret == "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        assert get_password_history(account_id, new_key)[0]["password"] == "AncienSecret!"
        assert get_master_config() == (
            base64.b64encode(new_salt).decode("utf-8"),
            new_hash,
        )

    def test_change_invalide_annule_toute_la_transaction(
        self, tmp_db, master_password, salt, encryption_key
    ):
        import base64
        import pytest
        from src.crypto import create_verification_hash, derive_key, generate_salt
        from src.database import (
            add_account,
            change_master_password,
            get_all_accounts,
            get_connection,
            save_master_config,
        )
        from src.history import push_password_history

        save_master_config(
            base64.b64encode(salt).decode("utf-8"),
            create_verification_hash(master_password, salt),
        )
        account_id = add_account(
            "Compte de test", "demo@example.invalid", "Secret intact!",
            "", "", None, encryption_key,
        )
        push_password_history(account_id, "Historique!", encryption_key)
        conn = get_connection()
        conn.execute(
            "UPDATE password_history SET password_encrypted = 'invalid' WHERE account_id = ?",
            (account_id,),
        )
        conn.commit()
        conn.close()

        new_salt = generate_salt()
        new_key = derive_key("NewDebugMaster42!", new_salt)
        with pytest.raises(Exception):
            change_master_password(
                "NewDebugMaster42!",
                new_salt,
                create_verification_hash("NewDebugMaster42!", new_salt),
                encryption_key,
                new_key,
            )

        assert get_all_accounts(encryption_key)[0].password == "Secret intact!"
