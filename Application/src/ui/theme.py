"""
Système de thème pour VaultApp.

Définit toutes les couleurs, polices et constantes du design.
Deux modes : sombre (par défaut) et clair.

Chaque couleur est pensée pour être agréable à l'œil et cohérente.
"""

# ══════════════════════════════════════════════════════════════
# Palette de couleurs
# ══════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        # Arrière-plans
        "bg_primary": "#0f0f13",         # Fond principal (très sombre)
        "bg_secondary": "#1a1a24",       # Sidebar, cartes
        "bg_tertiary": "#252533",        # Champs de saisie, survol
        "bg_hover": "#2d2d3f",           # Survol des éléments
        "bg_active": "#363649",          # Élément sélectionné
        "bg_card": "#1e1e2e",            # Cartes de comptes
        "bg_dialog": "#1a1a24",          # Fond des dialogues
        "bg_input": "#252533",           # Champs de texte
        
        # Texte
        "text_primary": "#e4e4ed",       # Texte principal
        "text_secondary": "#9494a8",     # Texte secondaire / labels
        "text_muted": "#5e5e72",         # Texte très discret
        "text_on_accent": "#ffffff",     # Texte sur bouton accent
        
        # Accent (violet/indigo)
        "accent": "#7c5cfc",             # Couleur principale
        "accent_hover": "#6a4bea",       # Survol accent
        "accent_light": "#1d173d",       # Accent mélangé (solide)
        "accent_glow": "#2a1e5c",        # Lueur mélangée (solide)
        
        # États
        "success": "#22c55e",
        "warning": "#eab308",
        "error": "#ef4444",
        "error_light": "#2e141c",       # Rouge mélangé (solide)
        "info": "#3b82f6",
        
        # Bordures
        "border": "#2a2a3a",
        "border_light": "#353548",
        "border_focus": "#7c5cfc",
        
        # Scrollbar
        "scrollbar": "#353548",
        "scrollbar_hover": "#454558",
        
        # Ombres (effet glassmorphism)
        "shadow": "#00000060",
    },
    "light": {
        # Arrière-plans
        "bg_primary": "#f5f5f9",
        "bg_secondary": "#ffffff",
        "bg_tertiary": "#eeeef4",
        "bg_hover": "#e8e8f0",
        "bg_active": "#dedee8",
        "bg_card": "#ffffff",
        "bg_dialog": "#ffffff",
        "bg_input": "#f0f0f6",
        
        # Texte
        "text_primary": "#1a1a2e",
        "text_secondary": "#6b6b80",
        "text_muted": "#9e9eb0",
        "text_on_accent": "#ffffff",
        
        # Accent
        "accent": "#6c4feb",
        "accent_hover": "#5a3dd8",
        "accent_light": "#f1edfd",       # Accent mélangé (solide)
        "accent_glow": "#e6dbfa",        # Lueur mélangée (solide)
        
        # États
        "success": "#16a34a",
        "warning": "#ca8a04",
        "error": "#dc2626",
        "error_light": "#fcecee",       # Rouge mélangé (solide)
        "info": "#2563eb",
        
        # Bordures
        "border": "#e2e2ec",
        "border_light": "#ededf4",
        "border_focus": "#6c4feb",
        
        # Scrollbar
        "scrollbar": "#d0d0dc",
        "scrollbar_hover": "#b8b8c8",
        
        # Ombres
        "shadow": "#00000015",
    }
}


def blend_colors(fg_color, bg_color, alpha: float):
    """
    Mélange fg_color et bg_color avec une opacité alpha (0.0 à 1.0).
    Gère les chaînes simples et les tuples de couleur CustomTkinter.
    """
    def _blend(fg_hex: str, bg_hex: str) -> str:
        try:
            fg = fg_hex.lstrip('#')
            bg = bg_hex.lstrip('#')
            if len(fg) == 3: fg = "".join([c*2 for c in fg])
            if len(bg) == 3: bg = "".join([c*2 for c in bg])
            r = max(0, min(255, int(alpha * int(fg[0:2], 16) + (1 - alpha) * int(bg[0:2], 16))))
            g = max(0, min(255, int(alpha * int(fg[2:4], 16) + (1 - alpha) * int(bg[2:4], 16))))
            b = max(0, min(255, int(alpha * int(fg[4:6], 16) + (1 - alpha) * int(bg[4:6], 16))))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return fg_hex
            
    is_fg_tuple = isinstance(fg_color, tuple) or isinstance(fg_color, list)
    is_bg_tuple = isinstance(bg_color, tuple) or isinstance(bg_color, list)
    
    if is_fg_tuple and is_bg_tuple:
        return (_blend(fg_color[0], bg_color[0]), _blend(fg_color[1], bg_color[1]))
    elif is_fg_tuple:
        return (_blend(fg_color[0], bg_color), _blend(fg_color[1], bg_color))
    elif is_bg_tuple:
        return (_blend(fg_color, bg_color[0]), _blend(fg_color, bg_color[1]))
    else:
        return _blend(fg_color, bg_color)


# ══════════════════════════════════════════════════════════════
# Polices
# ══════════════════════════════════════════════════════════════

FONTS = {
    "heading_xl": ("Segoe UI", 28, "bold"),
    "heading_lg": ("Segoe UI", 22, "bold"),
    "heading": ("Segoe UI", 18, "bold"),
    "heading_sm": ("Segoe UI", 15, "bold"),
    "body": ("Segoe UI", 13),
    "body_bold": ("Segoe UI", 13, "bold"),
    "body_sm": ("Segoe UI", 11),
    "body_sm_bold": ("Segoe UI", 11, "bold"),
    "caption": ("Segoe UI", 10),
    "icon_lg": ("Segoe UI Emoji", 24),
    "icon": ("Segoe UI Emoji", 18),
    "icon_sm": ("Segoe UI Emoji", 14),
    "mono": ("Consolas", 13),
}


# ══════════════════════════════════════════════════════════════
# Dimensions
# ══════════════════════════════════════════════════════════════

DIMENSIONS = {
    "window_width": 1100,
    "window_height": 720,
    "sidebar_width": 260,
    "card_height": 80,
    "corner_radius": 12,
    "corner_radius_sm": 8,
    "corner_radius_lg": 16,
    "padding": 16,
    "padding_sm": 8,
    "padding_lg": 24,
    "padding_xl": 32,
    "button_height": 40,
    "input_height": 42,
    "icon_size": 40,
}


# ══════════════════════════════════════════════════════════════
# Gestionnaire de thème
# ══════════════════════════════════════════════════════════════

class ThemeManager:
    """
    Gère le thème actif sous forme de tuples (light, dark) pour CustomTkinter.
    """
    
    def get(self, key: str):
        """Récupère une couleur sous forme de tuple (light, dark)."""
        light_color = THEMES["light"].get(key, "#ff00ff")
        dark_color = THEMES["dark"].get(key, "#ff00ff")
        return (light_color, dark_color)
    
    def is_dark(self) -> bool:
        """Vérifie si le mode sombre est actif."""
        import customtkinter as ctk
        return ctk.get_appearance_mode().lower() == "dark"
    
    def toggle(self):
        """Bascule le thème entre sombre et clair."""
        import customtkinter as ctk
        new_mode = "light" if self.is_dark() else "dark"
        ctk.set_appearance_mode(new_mode)
        return new_mode


# Instance globale du thème (partagée par toute l'application)
theme = ThemeManager()
