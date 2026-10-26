"""
API locale Flask pour VaultApp — Communication avec l'extension navigateur.

L'API tourne sur localhost:27842 et expose 3 endpoints :

  GET  /status            → vérifie que VaultApp est lancée et déverrouillée
  GET  /accounts?url=...  → retourne les comptes correspondant à une URL
  POST /fill              → signal que l'autofill a été demandé (optionnel)

Sécurité :
- Écoute uniquement sur 127.0.0.1 (pas accessible depuis le réseau)
- L'app doit être déverrouillée (encryption_key présente) pour répondre
- CORS restreint à l'extension (chrome-extension:// et moz-extension://)
- Les mots de passe ne sont jamais envoyés dans /accounts — seulement ID + nom
- /fill retourne le login et le mot de passe après sélection du compte

Usage :
    from src.api import VaultAPI
    api = VaultAPI()
    api.set_key(encryption_key)  # après déverrouillage
    api.start()                  # démarre dans un thread daemon
    api.clear_key()              # lors du verrouillage
    api.stop()                   # à la fermeture de l'app
"""

import threading
import logging
from typing import Optional
from urllib.parse import urlparse

# Désactiver les logs Flask/Werkzeug pour ne pas polluer la console
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

PORT = 27842
HOST = "127.0.0.1"


class VaultAPI:
    """
    Serveur Flask léger qui tourne en arrière-plan dans un thread daemon.
    
    L'encryption_key est partagée de façon thread-safe via un verrou.
    """

    def __init__(self):
        self._key: Optional[bytes] = None
        self._key_lock = threading.Lock()
        self._server_thread: Optional[threading.Thread] = None
        self._app = self._create_app()

    # ── Gestion de la clé ────────────────────────────────────

    def set_key(self, key: bytes):
        """Appeler après déverrouillage de l'app."""
        with self._key_lock:
            self._key = key

    def clear_key(self):
        """Appeler lors du verrouillage ou de la fermeture."""
        with self._key_lock:
            self._key = None

    def _get_key(self) -> Optional[bytes]:
        with self._key_lock:
            return self._key

    # ── Cycle de vie ─────────────────────────────────────────

    def start(self):
        """Démarre le serveur Flask dans un thread daemon."""
        if self._server_thread and self._server_thread.is_alive():
            return  # Déjà démarré

        self._server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,   # s'arrête quand l'app principale s'arrête
            name="VaultAPI",
        )
        self._server_thread.start()

    def stop(self):
        """Arrête le serveur (la fermeture de l'app suffit grâce au daemon)."""
        self.clear_key()

    def _run_server(self):
        """Lance Flask — appelé dans le thread daemon."""
        self._app.run(host=HOST, port=PORT, threaded=True, use_reloader=False)

    # ── Application Flask ─────────────────────────────────────

    def _create_app(self):
        try:
            from flask import Flask, jsonify, request
        except ImportError:
            # Flask non installé — l'API ne sera pas disponible
            return None

        app = Flask(__name__)

        def _cors_headers(response):
            """Autorise uniquement les extensions navigateur."""
            origin = request.headers.get("Origin", "")
            if origin.startswith("chrome-extension://") or origin.startswith("moz-extension://"):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response

        app.after_request(_cors_headers)

        # ── OPTIONS (preflight CORS) ──────────────────────────
        @app.route("/<path:path>", methods=["OPTIONS"])
        def options_handler(path):
            return jsonify({}), 200

        # ── GET /status ───────────────────────────────────────
        @app.route("/status", methods=["GET"])
        def status():
            """
            Indique si VaultApp est lancée et déverrouillée.
            
            Réponse :
                { "running": true, "unlocked": true|false }
            """
            return jsonify({
                "running": True,
                "unlocked": self._get_key() is not None,
                "version": 2,
            })

        # ── GET /accounts?url=https://... ────────────────────
        @app.route("/accounts", methods=["GET"])
        def accounts():
            """
            Retourne les comptes dont l'URL correspond au domaine demandé.
            
            Paramètre : url (ex: https://github.com/login)
            
            Réponse :
                {
                  "unlocked": true,
                  "accounts": [
                    { "id": 1, "name": "GitHub", "login": "user@test.com",
                      "category_icon": "💻", "category_color": "#3b82f6" }
                  ]
                }
            
            Note : les mots de passe ne sont PAS inclus ici pour minimiser
            l'exposition. L'extension doit appeler /fill pour obtenir le mdp
            d'un compte spécifique.
            """
            key = self._get_key()
            if key is None:
                return jsonify({"unlocked": False, "accounts": []}), 403

            url_param = request.args.get("url", "").strip()
            domain = _extract_domain(url_param)

            if not domain:
                return jsonify({"unlocked": True, "accounts": []})

            try:
                from src import database as db
                all_accounts = db.get_all_accounts(key, search_query=domain)
                result = [
                    {
                        "id": a.id,
                        "name": a.name,
                        "login": a.login,
                        "url": a.url,
                        "category_icon": a.category_icon,
                        "category_color": a.category_color,
                    }
                    for a in all_accounts
                    if _account_url_matches_domain(a.url, domain)
                ]
                return jsonify({"unlocked": True, "accounts": result})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ── POST /fill ────────────────────────────────────────
        @app.route("/fill", methods=["POST"])
        def fill():
            """
            Retourne le login + mot de passe d'un compte spécifique.
            
            Body JSON : { "account_id": 42 }
            
            Réponse :
                {
                  "login": "user@example.com",
                  "password": "MonMotDePasse123!"
                }
            
            Sécurité : ne fonctionne que si l'app est déverrouillée.
            """
            key = self._get_key()
            if key is None:
                return jsonify({"error": "VaultApp est verrouillée"}), 403

            data = request.get_json(silent=True) or {}
            account_id = data.get("account_id")

            if isinstance(account_id, bool) or not isinstance(account_id, int):
                return jsonify({"error": "account_id manquant ou invalide"}), 400

            try:
                from src import database as db
                accounts = db.get_all_accounts(key)
                account = next((a for a in accounts if a.id == account_id), None)

                if account is None:
                    return jsonify({"error": "Compte introuvable"}), 404

                return jsonify({
                    "login": account.login,
                    "password": account.password,
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        return app


def _extract_domain(url: str) -> str:
    """
    Extrait le domaine principal d'une URL.
    
    Exemples :
        https://github.com/login  →  github.com
        https://www.netflix.com   →  netflix.com
        github.com                →  github.com
    """
    if not url:
        return ""
    try:
        if "://" not in url:
            url = "https://" + url
        parsed = urlparse(url)
        host = parsed.hostname or ""
        # Supprimer le www.
        if host.startswith("www."):
            host = host[4:]
        return host.lower()
    except Exception:
        return ""


def _account_url_matches_domain(account_url: str, requested_domain: str) -> bool:
    """Match a stored host only on a domain boundary; blank URLs are global."""
    if not account_url:
        return True

    account_domain = _extract_domain(account_url)
    if not account_domain:
        return False

    return (
        account_domain == requested_domain
        or account_domain.endswith("." + requested_domain)
        or requested_domain.endswith("." + account_domain)
    )


# ── Singleton global ─────────────────────────────────────────

# Instance partagée utilisée par app.py
vault_api = VaultAPI()
