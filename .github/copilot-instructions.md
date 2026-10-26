# Copilot instructions for VaultApp

When responding to the repository owner, use French by default; keep code symbols, commands, and API names in their original form.

## Repository structure

This repository is split between a desktop app and a browser extension:

- `Application/` contains the Python desktop application.
- `Extension/` contains the Chrome/Firefox browser extension.
- The desktop app exposes a local Flask API on `127.0.0.1:27842` for the browser extension to query.
- The primary persistent data store is a local SQLite database in `%APPDATA%\VaultApp\vault.db`.

## Build, test, and validation commands

Run commands from the `Application/` directory unless noted otherwise.

- Launch the desktop app:
  - `python main.py`
- Launch the isolated disposable debug vault (no startup password prompt):
  - `python main.py --debug`
  - Uses a temporary `%APPDATA%` directory with fake data, does not start the browser API, and disables clipboard copies.
  - On Windows, `Application/run_debug.bat` opens a dedicated console with click expectations and uncaught Tk callback errors.
- Install Python dependencies:
  - `python -m pip install -r requirements.txt`
- Full unit suite:
  - `python -m pytest tests/test_unit.py -v`
- Full project test suite (includes integration/regression checks):
  - `python -m pytest tests/ -v`
- Single test selection:
  - `python -m pytest tests/test_unit.py::TestCrypto::test_encrypt_decrypt_roundtrip -v`
  - `python -m pytest tests/test_unit.py -k generate_password -v`
- Package/build the desktop app:
  - `python build.py`
  - This script runs the full `tests/` suite first and then bundles the app with PyInstaller into `dist/VaultApp.exe`.
- Create the Windows installer after packaging:
  - Open `installer.iss` with Inno Setup Compiler from `Application/`; it expects `dist/VaultApp.exe`.

There is no separate lint configuration or formatter in this repo at the moment; `pytest` is the main validation gate.

The pytest fixtures in `tests/conftest.py` redirect the database path to a fresh temporary SQLite file. Keep tests isolated this way; do not let tests read or modify a developer's real `%APPDATA%\VaultApp\vault.db`.

## High-level architecture

### 1) Desktop application (`Application/`)

- `main.py` starts `src.ui.app.VaultApp`.
- `src/ui/` contains the desktop screens (welcome, unlock, main screens, etc.).
- `src.database.py` initializes and manages the local SQLite database, including:
  - `config` for master-password metadata,
  - `categories`,
  - `accounts` with encrypted password data.
- `src.crypto.py` owns the key-derivation and encryption/decryption logic.
- `src.api.py` starts a small Flask server in a daemon thread. It listens only on loopback and is used by the browser extension to query account data and request autofill.
- `src.history.py`, `src.generator.py`, `src.strength.py`, `src.clipboard.py`, and `src.vault_io.py` implement password history, generation, strength checks, clipboard handling, and encrypted backup import/export.
- `src.ui.app.VaultApp` initializes persistence and the history table, starts the API while locked, and routes between the welcome/login/locked and main screens. The main screen owns account/category navigation, the security dashboard, auto-lock activity timer, and settings dialogs.

### Startup, unlock, and encrypted data

- On first launch, `LoginScreen` creates a random salt, stores the salt and a master-password verification value in `config`, creates default categories, and derives the vault key. On later launches it checks the verification value before deriving the key.
- `src.crypto.py` derives a 32-byte key with PBKDF2-HMAC-SHA256 (600,000 iterations), then uses AES-GCM with a fresh 12-byte nonce for each encrypted value.
- Account passwords and notes are encrypted before being written to SQLite. Account names, logins, URLs, category metadata, and settings are stored as ordinary SQLite values; do not assume every field is encrypted.
- SQLite is opened through `src.database.get_connection()`, which enables WAL mode and foreign keys. The database path is `%APPDATA%\VaultApp\vault.db` (falling back to the user's home directory if `APPDATA` is unset).
- Password history is a separate `password_history` table created by `src.history.init_password_history_table()`. It stores encrypted previous passwords and is limited to three entries per account. Account edits push the previous password into history only when the password changes; deleting an account cascades to its history.
- `src.vault_io.py` exports a `VAULT2`-header file containing an AES-GCM-encrypted JSON payload. Import replaces accounts and categories; the settings/master-password config are not part of that payload.
- Changing the master password must keep the stored salt, verification value, derived key, account ciphertext, and password-history ciphertext consistent. Review every encrypted table when changing key-rotation behavior.

### Desktop features and shared helpers

- `src.ui.main_screen.MainScreen` is the central UI controller. It refreshes account cards and category buttons from the database, and delegates editing to `AccountDialog` / `CategoryDialog`.
- The dashboard (`src.ui.dashboard_screen.DashboardScreen`) evaluates password strength, reused passwords, and age (180 days) and computes an overall score via `src.strength.calculate_vault_score()`.
- Strength analysis uses `zxcvbn` when installed and a local heuristic otherwise. Password generation uses Python's `secrets` module and guarantees one character from every enabled group.
- Password copy is scheduled to clear the clipboard after 30 seconds; login copy intentionally does not use that timer. Keep this distinction if changing clipboard behavior.
- Theme colors, fonts, and dimensions are centralized in `src.ui.theme`; screens and shared widgets consume those values through the shared `theme` manager.

### Browser extension (`Extension/`)

- `Extension/background.js` is the browser-side service worker.
- `Extension/content.js` runs on pages and fills form fields.
- `Extension/popup.js` and `popup.html` expose the extension UI.
- The extension calls the local API at `http://127.0.0.1:27842`:
  - `GET /status` to verify VaultApp is running and unlocked.
  - `GET /accounts?url=...` to fetch matching accounts for the current site.
  - `POST /fill` to retrieve a password for a selected account.
- The password is intentionally not exposed by `/accounts`; it is only returned by `/fill` for a specific account.

### Security model

- The Flask server binds to `127.0.0.1:27842`; do not change it to a network-facing host as part of routine extension work.
- CORS response headers are added for Chrome and Mozilla extension origins, but CORS is not authentication and does not prevent local non-browser clients from reaching a loopback service.
- `/status` reports the lock state. `/accounts` requires an unlocked vault and returns account metadata, not passwords. `POST /fill` requires an unlocked vault and returns the selected account's login and password; do not describe it as single-use or assume the API clears a password buffer.
- Match stored account URLs by hostname/domain boundaries, not arbitrary substring, to avoid exposing a credential for a lookalike domain. Blank account URLs intentionally match any domain.
- The extension popup requests `/fill` only after the user selects a matching account, then sends the credentials to the content script. `content.js` fills visible password fields and tries to find a nearby login field.
- Treat changes to account selection, endpoint responses, CORS, host binding, extension permissions, or autofill as changes to one shared app/browser security boundary.

## Key conventions in this codebase

- Keep the browser-extension and desktop-app contracts aligned. Changes to `Application/src/api.py` and `Extension/popup.js` / `Extension/content.js` should be kept in sync.
- Treat the database layer (`src/database.py`) as the source of truth for encrypted account and category records. Use the existing helper functions instead of reaching directly into SQLite in new code.
- Maintain the current separation between local-only API access and user-visible password data. Do not broaden the response surface of `/accounts` beyond metadata unless the security model is intentionally changed.
- The project explicitly validates with `pytest` before package builds; `build.py` runs the test suite before creating the Windows executable.
- The extension is built for Chrome and Firefox, but the runtime contract is the same: local API on `127.0.0.1:27842` with browser extension permissions and CORS restricted to extension origins.
- Document changes in the behavior of the browser-extension/local-app handshake in the same area where the API or extension scripts are updated.
- Test database-backed behavior with `tmp_db` / `db_with_data` fixtures; they isolate SQLite per test and initialize the schema plus password-history table.
- The automated suite covers Python crypto, database CRUD, history, import/export, security scoring, regression behavior, and import smoke tests. It does not execute the browser extension or GUI interactively, so those changes need a manual smoke test in the target browser/app.
- The Chrome MV3 manifest is `Extension/manifest.json`; the Firefox MV2 manifest is `Extension/manifest_firefox.json`. There is also a duplicate root-level `manifest.json`; prefer the manifests in `Extension/` and keep icon paths relative to that directory.

## Practical guidance for future edits

- When changing encrypted data or password flows, validate both the database logic and the API response contract.
- For UI work, prefer updating the existing screen patterns and theme flow instead of introducing a second app framework or custom styling system.
- For app-packaging or installer-related changes, check `Application/build.py` and `Application/VaultApp.spec` before editing packaging configuration.

## Existing project documentation used

- `Extension/README.md` describes the extension installation and runtime contract.
- `Application/build.py` documents the expected build flow and pre-flight tests.
- `Application/tests/*.py` define the project’s real validation expectations.
- For a French-language explanation of these repository-specific details, see [copilot-francais-pour-dev.md](./copilot-francais-pour-dev.md).
