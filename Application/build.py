"""
Script de build pour VaultApp V2.

Avant de builder :
    python -m pytest tests/ -v   ← lance les 93 tests (doit être 100% vert)

Usage :
    python build.py

Le .exe sera créé dans dist/VaultApp.exe
"""

import subprocess
import sys
import os


def run_tests():
    print("Lancement des tests avant le build...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    if result.returncode != 0:
        print("\nLes tests ont échoué — build annulé.")
        print("Corrige les erreurs avant de relancer build.py.")
        sys.exit(1)
    print("\nTous les tests passent — build en cours...\n")


def build():
    print("=" * 50)
    print("Build VaultApp V2")
    print("=" * 50)

    # Vérifier PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} trouvé")
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Chemin de l'icône
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "assets", "logo.ico")
    icon_exists = os.path.exists(icon_path)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=VaultApp",
        "--onefile",                    # Un seul .exe standalone
        "--windowed",                   # Pas de console noire
        "--noconfirm",
        "--clean",

        # Icône (le logo VaultApp)
        *(["--icon=assets/logo.ico"] if icon_exists else []),

        # Modules cachés
        "--hidden-import=customtkinter",
        "--hidden-import=pyperclip",
        "--hidden-import=PIL",
        "--hidden-import=flask",
        "--hidden-import=zxcvbn",

        # Données CustomTkinter (thèmes, polices)
        "--collect-all=customtkinter",

        "main.py",
    ]

    if not icon_exists:
        print("⚠️  assets/logo.ico introuvable — build sans icône")
    else:
        print(f"Icône : {icon_path}")

    print(f"Commande : {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        print()
        print("=" * 50)
        print("Build réussi !")
        print("   → dist/VaultApp.exe")
        print()
        print("Pour créer l'installeur Windows,")
        print("ouvre installer.iss avec Inno Setup Compiler.")
        print("=" * 50)
    else:
        print("\nErreur lors du build — vérifie les messages ci-dessus.")
        sys.exit(1)


if __name__ == "__main__":
    # Lancer les tests d'abord (commenter la ligne si besoin d'un build rapide)
    run_tests()
    build()
