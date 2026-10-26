"""Tests for the isolated, disposable debug vault."""

import base64
from types import SimpleNamespace

from src.crypto import verify_master_password
from src.database import (
    get_all_accounts,
    get_all_categories,
    get_master_config,
    get_setting,
)
from src.debug_data import DEBUG_MASTER_PASSWORD, create_debug_vault
from src.debug_console import expected_result_for


def test_debug_vault_uses_isolated_seeded_database(tmp_db):
    key = create_debug_vault()

    accounts = get_all_accounts(key)
    assert len(accounts) == 5
    assert {account.name for account in accounts} >= {
        "Demo faible",
        "Demo partagé A",
        "Demo partagé B",
        "Demo obsolète",
    }
    assert len(get_all_categories()) == 2
    assert get_setting("auto_lock_minutes") == "0"

    salt_b64, stored_hash = get_master_config()
    salt = base64.b64decode(salt_b64)
    assert verify_master_password(DEBUG_MASTER_PASSWORD, salt, stored_hash)

    old_account = next(account for account in accounts if account.name == "Demo obsolète")
    assert old_account.created_at[:10] < accounts[0].created_at[:10]


def test_debug_console_describes_expected_click_results():
    assert "formulaire d'ajout" in expected_result_for("＋ Ajouter").lower()
    assert "bloquée" in expected_result_for("🔑 Copier").lower()
    assert "confirmation" in expected_result_for("Supprimer").lower()
    assert "mode debug" in expected_result_for("Option inconnue").lower()


def test_debug_console_logs_click_and_expected_result(capsys):
    from src.debug_console import DebugConsole

    class FakeButton:
        master = None

        def cget(self, key):
            return "＋ Ajouter un compte"

    class FakeWindow:
        def title(self):
            return "VaultApp — MODE DEBUG"

    class FakeRoot:
        current_screen = SimpleNamespace()

        def after_idle(self, callback):
            callback()

        def winfo_exists(self):
            return True

        def focus_get(self):
            return SimpleNamespace(winfo_toplevel=lambda: FakeWindow())

        def title(self):
            return "VaultApp — MODE DEBUG"

    console = DebugConsole.__new__(DebugConsole)
    console.root = FakeRoot()
    console._click_number = 0
    console._on_click(SimpleNamespace(widget=FakeButton()))

    output = capsys.readouterr().out
    assert "[CLIC 001] ＋ Ajouter un compte" in output
    assert "[ATTENDU] Un formulaire d'ajout doit s'ouvrir." in output
    assert "[APRÈS CLIC]" in output
