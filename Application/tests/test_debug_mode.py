"""Tests for the isolated, disposable debug vault."""

import base64

from src.crypto import verify_master_password
from src.database import (
    get_all_accounts,
    get_all_categories,
    get_master_config,
    get_setting,
)
from src.debug_data import DEBUG_MASTER_PASSWORD, create_debug_vault


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
