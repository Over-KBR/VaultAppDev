"""
Gestion du presse-papier pour VaultApp.

Permet de copier un mot de passe ou un login dans le presse-papier
en un seul clic, et de le vider automatiquement après un délai.
"""

import threading
import pyperclip


def get_clipboard_clear_seconds() -> int:
    """Retourne le délai configuré avant l'effacement du presse-papiers."""
    from src.database import get_setting

    seconds = int(get_setting("clipboard_clear_seconds", "30"))
    if seconds not in (15, 30, 60):
        raise ValueError("Le délai d'effacement du presse-papiers est invalide.")
    return seconds


def copy_to_clipboard(text: str, clear_after_seconds: int = 30):
    """
    Copie un texte dans le presse-papier.
    
    Par sécurité, le presse-papier est vidé automatiquement après
    30 secondes (pour éviter qu'un mot de passe reste en mémoire).
    
    Args:
        text: Le texte à copier
        clear_after_seconds: Délai avant de vider le presse-papier (en secondes)
    """
    pyperclip.copy(text)
    
    # Programmer le nettoyage automatique
    if clear_after_seconds > 0:
        timer = threading.Timer(clear_after_seconds, _clear_clipboard, args=[text])
        timer.daemon = True  # Le timer s'arrête quand l'app se ferme
        timer.start()


def _clear_clipboard(original_text: str):
    """
    Vide le presse-papier seulement si son contenu n'a pas changé.
    
    Si l'utilisateur a copié autre chose entre-temps, on ne touche à rien.
    """
    try:
        current = pyperclip.paste()
        if current == original_text:
            pyperclip.copy("")
    except Exception:
        pass  # Pas grave si ça échoue