"""
VaultApp — Gestionnaire de mots de passe sécurisé
==================================================

Point d'entrée de l'application.
Lance la fenêtre principale.

Pour lancer l'app :
    python main.py

Pour lancer un coffre de démonstration temporaire et isolé :
    python main.py --debug
"""

import argparse
import os
import tempfile


def main():
    parser = argparse.ArgumentParser(description="Gestionnaire de mots de passe VaultApp")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Lance un coffre fictif temporaire sans toucher aux données réelles.",
    )
    args = parser.parse_args()

    if not args.debug:
        from src.ui.app import VaultApp

        VaultApp().mainloop()
        return

    with tempfile.TemporaryDirectory(prefix="vaultapp-debug-") as debug_appdata:
        os.environ["APPDATA"] = debug_appdata

        from src.debug_data import create_debug_vault
        from src.ui.app import VaultApp

        debug_key = create_debug_vault()
        VaultApp(debug_mode=True, debug_key=debug_key).mainloop()


if __name__ == "__main__":
    main()
