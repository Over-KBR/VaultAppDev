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
        "bg_primary": "#111318",
        "bg_secondary": "#171a21",
        "bg_tertiary": "#222630",
        "bg_hover": "#252a35",
        "bg_active": "#2d3340",
        "bg_card": "#191d25",
        "bg_dialog": "#191d25",
        "bg_input": "#11151b",
        "text_primary": "#f4f6fa",
        "text_secondary": "#b6bdca",
        "text_muted": "#858e9e",
        "text_on_accent": "#ffffff",
        "accent": "#70aaff",
        "accent_hover": "#8bbaff",
        "accent_light": "#202f48",
        "accent_glow": "#293d5a",
        "success": "#54d68a",
        "warning": "#f0bd62",
        "error": "#ff7777",
        "error_light": "#39272d",
        "info": "#75c8ee",
        "border": "#292e38",
        "border_light": "#39414e",
        "border_focus": "#70aaff",
        "scrollbar": "#4b5361",
        "scrollbar_hover": "#687284",
        "shadow": "#00000040",
    },
    "light": {
        "bg_primary": "#f4f5f7",
        "bg_secondary": "#fafbfc",
        "bg_tertiary": "#edf0f4",
        "bg_hover": "#e9edf3",
        "bg_active": "#dfe6f0",
        "bg_card": "#ffffff",
        "bg_dialog": "#ffffff",
        "bg_input": "#f7f8fa",
        "text_primary": "#1b2028",
        "text_secondary": "#596272",
        "text_muted": "#858e9c",
        "text_on_accent": "#ffffff",
        "accent": "#246bce",
        "accent_hover": "#1d5db7",
        "accent_light": "#e9f1fd",
        "accent_glow": "#dbe8fb",
        "success": "#16834f",
        "warning": "#a86a00",
        "error": "#c73d4b",
        "error_light": "#fbecef",
        "info": "#24719a",
        "border": "#e2e6ec",
        "border_light": "#d4dbe5",
        "border_focus": "#246bce",
        "scrollbar": "#c4cbd5",
        "scrollbar_hover": "#a9b3c1",
        "shadow": "#1e293b12",
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
    "heading_xl": ("Segoe UI Variable Display", 32, "bold"),
    "heading_lg": ("Segoe UI Variable Display", 27, "bold"),
    "heading": ("Segoe UI Variable Display", 24, "bold"),
    "heading_sm": ("Segoe UI Variable Text", 17, "bold"),
    "body_lg": ("Segoe UI Variable Text", 15),
    "body": ("Segoe UI Variable Text", 14),
    "body_bold": ("Segoe UI Variable Text", 14, "bold"),
    "body_sm": ("Segoe UI Variable Text", 13),
    "body_sm_bold": ("Segoe UI Variable Text", 13, "bold"),
    "caption": ("Segoe UI Variable Text", 11),
    "label": ("Segoe UI Variable Text", 10, "bold"),
    "mono": ("Consolas", 13),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 18,
    "xl": 24,
    "xxl": 32,
}

MOTION = {
    "fast_ms": 90,
    "standard_ms": 160,
    "emphasis_ms": 220,
    "reduced": False,
}

BUTTON_STYLES = {
    "primary": ("accent", "accent_hover", "text_on_accent", None),
    "secondary": ("bg_tertiary", "bg_hover", "text_primary", "border"),
    "quiet": ("transparent", "bg_hover", "text_secondary", None),
    "destructive": ("error_light", "error", "error", None),
}


def button_style(variant="secondary", height=None, corner_radius=None):
    """Options cohérentes pour les boutons CustomTkinter."""
    if variant not in BUTTON_STYLES:
        raise ValueError(f"Style de bouton inconnu : {variant}")
    fg, hover, text, border = BUTTON_STYLES[variant]
    style = {
        "fg_color": "transparent" if fg == "transparent" else theme.get(fg),
        "hover_color": theme.get(hover),
        "text_color": theme.get(text),
        "border_width": 1 if border else 0,
    }
    if border:
        style["border_color"] = theme.get(border)
    if height is not None:
        style["height"] = height
    style["corner_radius"] = (
        corner_radius if corner_radius is not None
        else DIMENSIONS["corner_radius_sm"]
    )
    return style


def entry_style(height=None):
    """Options cohérentes pour les champs de saisie CustomTkinter."""
    style = {
        "fg_color": theme.get("bg_input"),
        "border_color": theme.get("border"),
        "text_color": theme.get("text_primary"),
        "placeholder_text_color": theme.get("text_muted"),
        "corner_radius": DIMENSIONS["corner_radius_sm"],
        "height": height if height is not None else DIMENSIONS["input_height"],
    }
    return style


def bind_entry_focus(entry):
    """Affiche un contour accentué lorsque le champ reçoit le focus clavier."""
    entry.bind(
        "<FocusIn>",
        lambda _event: entry.configure(border_color=theme.get("border_focus")),
        add="+",
    )
    entry.bind(
        "<FocusOut>",
        lambda _event: entry.configure(border_color=theme.get("border")),
        add="+",
    )

# ══════════════════════════════════════════════════════════════
# Dimensions
# ══════════════════════════════════════════════════════════════

DIMENSIONS = {
    "window_width": 1240,
    "window_height": 800,
    "sidebar_width": 244,
    "card_height": 82,
    "corner_radius": 12,
    "corner_radius_sm": 8,
    "corner_radius_lg": 16,
    "padding": 18,
    "padding_sm": 8,
    "padding_lg": 24,
    "padding_xl": 32,
    "button_height": 42,
    "input_height": 44,
    "icon_size": 42,
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
