"""
VaultApp — Gestionnaire de mots de passe sécurisé
==================================================

Point d'entrée de l'application.
Lance la fenêtre principale.

Pour lancer l'app :
    python main.py
"""

from src.ui.app import VaultApp


def main():
    app = VaultApp()
    app.mainloop()


if __name__ == "__main__":
    main()
