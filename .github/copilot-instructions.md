# Copilot instructions for VaultApp

## Repository structure

This repository is split between a desktop app and a browser extension:

- `Application/` contains the Python desktop application.
- `Extension/` contains the Chrome/Firefox browser extension.
- The desktop app exposes a local Flask API on `127.0.0.1:27842` for the browser extension to query.
- The primary persistent data store is a local SQLite database in `%APPDATA%\VaultApp\vault.db`.

## Build, test, and validation commands

Run commands from the `Application/` directory unless noted otherwise.

- Full unit suite:
  - `python -m pytest tests/test_unit.py -v`
- Full project test suite (includes integration/regression checks):
  - `python -m pytest tests/ -v`
- Single test selection:
  - `python -m pytest tests/test_unit.py -k crypto -v`
  - `python -m pytest tests/test_unit.py -k generate_password -v`
- Package/build the desktop app:
  - `python build.py`
  - This script runs the tests first and then bundles the app with PyInstaller into `dist/VaultApp.exe`.

There is no separate lint configuration or formatter in this repo at the moment; `pytest` is the main validation gate.

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
- `src.history.py`, `src.generator.py`, `src.strength.py`, and related modules fill supporting roles for password history, generation, and strength checks.

### 2) Browser extension (`Extension/`)

- `Extension/background.js` is the browser-side service worker.
- `Extension/content.js` runs on pages and fills form fields.
- `Extension/popup.js` and `popup.html` expose the extension UI.
- The extension calls the local API at `http://127.0.0.1:27842`:
  - `GET /status` to verify VaultApp is running and unlocked.
  - `GET /accounts?url=...` to fetch matching accounts for the current site.
  - `POST /fill` to retrieve a password for a selected account.
- The password is intentionally not exposed by `/accounts`; it is only returned by `/fill` for a specific account.

### 3) Security model

- All communication stays on localhost; the app is not designed for remote network access.
- Only the loopback interface is used.
- Passwords are stored encrypted in the database and are only exposed to the extension after the application is unlocked.

## Key conventions in this codebase

- Keep the browser-extension and desktop-app contracts aligned. Changes to `src/api.py` and the browser-side request/response flow should be kept in sync.
- Treat the database layer (`src/database.py`) as the source of truth for encrypted account and category records. Use the existing helper functions instead of reaching directly into SQLite in new code.
- Maintain the current separation between local-only API access and user-visible password data. Do not broaden the response surface of `/accounts` beyond metadata unless the security model is intentionally changed.
- The project explicitly validates with `pytest` before package builds; `build.py` runs the test suite before creating the Windows executable.
- The extension is built for Chrome and Firefox, but the runtime contract is the same: local API on `127.0.0.1:27842` with browser extension permissions and CORS restricted to extension origins.
- Document changes in the behavior of the browser-extension/local-app handshake in the same area where the API or extension scripts are updated.

## Practical guidance for future edits

- When changing encrypted data or password flows, validate both the database logic and the API response contract.
- For UI work, prefer updating the existing screen patterns and theme flow instead of introducing a second app framework or custom styling system.
- For app-packaging or installer-related changes, check `Application/build.py` and `Application/VaultApp.spec` before editing packaging configuration.

## Existing project documentation used

- `Extension/README.md` describes the extension installation and runtime contract.
- `Application/build.py` documents the expected build flow and pre-flight tests.
- `Application/tests/*.py` define the project’s real validation expectations.
