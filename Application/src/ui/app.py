"""
Fenêtre principale de VaultApp.

Gère la navigation entre les écrans :
1. Écran de déverrouillage (login)
2. Écran principal (après déverrouillage)

Gère aussi le changement de thème global.
"""

import customtkinter as ctk
from src.ui.theme import theme, DIMENSIONS
from src.ui.login_screen import LoginScreen
from src.ui.main_screen import MainScreen
from src.database import init_database, get_setting
from src.history import init_password_history_table
from src.ui.lock_screen import LockScreen
from src.ui.welcome_screen import WelcomeScreen
from src.api import vault_api


class VaultApp(ctk.CTk):
    """Fenêtre principale de l'application."""
    
    def __init__(self, debug_mode: bool = False, debug_key: bytes = None):
        super().__init__()
        if debug_mode and debug_key is None:
            raise ValueError("Le mode debug nécessite une clé de coffre temporaire.")

        self.debug_mode = debug_mode
        self.debug_key = debug_key
        
        # ── Configuration de la fenêtre ──
        self.title("VaultApp — Gestionnaire de mots de passe")
        self.geometry(f"{DIMENSIONS['window_width']}x{DIMENSIONS['window_height']}")
        self.minsize(900, 600)
        
        # Thème CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Couleur de fond
        self.configure(fg_color=theme.get("bg_primary"))
        
        # Centrer la fenêtre
        self._center_window()
        
        # ── Initialiser la base de données ──
        init_database()
        init_password_history_table()

        # Appliquer le thème sauvegardé
        saved_theme = get_setting("default_theme", "dark")
        ctk.set_appearance_mode(saved_theme)
        
        # ── Écran actuel ──
        self.current_screen = None
        self.encryption_key = None
        
        # Le mode debug ne doit pas exposer son coffre fictif à l'extension.
        if not self.debug_mode:
            vault_api.start()

        if self.debug_mode:
            self.title("VaultApp — MODE DEBUG (coffre temporaire)")
            self._show_main(self.debug_key)
        else:
            self._show_welcome()
    
    def _center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.update_idletasks()
        w = DIMENSIONS['window_width']
        h = DIMENSIONS['window_height']
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
    
    def _clear_screen(self):
        """Supprime l'écran actuel."""
        if self.current_screen:
            self.current_screen.destroy()
            self.current_screen = None
    
    def _show_welcome(self):
        """Affiche l'écran de bienvenue au démarrage."""
        self._clear_screen()
        self.current_screen = WelcomeScreen(
            self,
            on_continue=self._on_unlock,
        )
        self.current_screen.pack(fill="both", expand=True)

    def _show_login(self):
        """Affiche l'écran de verrouillage."""
        vault_api.clear_key()
        self._clear_screen()
        self.current_screen = LockScreen(
            self,
            on_unlock=self._on_unlock,
        )
        self.current_screen.pack(fill="both", expand=True)
    
    def _on_unlock(self, encryption_key=None):
        if self.debug_mode:
            self._show_main(encryption_key or self.debug_key)
            return
        if encryption_key:
            self._show_main(encryption_key)
        else:
            self._clear_screen()
            self.current_screen = LoginScreen(
                self,
                on_unlock=self._show_main,
            )
            self.current_screen.pack(fill="both", expand=True)
    
    def _show_main(self, encryption_key: bytes = None):
        """Affiche l'écran principal."""
        if encryption_key:
            self.encryption_key = encryption_key
        if not self.debug_mode:
            vault_api.set_key(self.encryption_key)
        self._clear_screen()
        self.current_screen = MainScreen(
            self,
            encryption_key=self.encryption_key,
            on_theme_toggle=self._toggle_theme,
            debug_mode=self.debug_mode,
        )
        self.current_screen.pack(fill="both", expand=True)

    def _debug_unlock(self, encryption_key: bytes):
        self.debug_key = encryption_key
        self._show_login()
    
    def _toggle_theme(self):
        """Bascule entre thème sombre et clair."""
        theme.toggle()
        
        # Mettre à jour la fenêtre
        self.configure(fg_color=theme.get("bg_primary"))
        
        # Rafraîchir l'écran principal
        if isinstance(self.current_screen, MainScreen):
            self.current_screen.apply_theme()
