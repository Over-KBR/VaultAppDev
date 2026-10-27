"""Lucide icon resources and shared CustomTkinter icon widgets."""

from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageColor

from src.ui.theme import DIMENSIONS, FONTS, theme


_ICON_ROOT = Path(__file__).resolve().parents[2] / "assets" / "icons"
_RASTER_ROOT = _ICON_ROOT / "png"

ICON_NAMES = frozenset({
    "activity",
    "arrow-left",
    "award",
    "banknote",
    "bird",
    "book-open",
    "briefcase-business",
    "building-2",
    "camera",
    "car-front",
    "chart-no-axes-column-increasing",
    "chart-pie",
    "chevron-right",
    "circle-check",
    "circle-help",
    "circle-x",
    "clapperboard",
    "clipboard-list",
    "cloud",
    "copy",
    "credit-card",
    "dice-5",
    "download",
    "eye",
    "eye-off",
    "fingerprint",
    "flask-conical",
    "folder",
    "gamepad-2",
    "gem",
    "gift",
    "globe",
    "graduation-cap",
    "heart",
    "heart-pulse",
    "headphones",
    "hotel",
    "house",
    "hospital",
    "inbox",
    "info",
    "key-round",
    "landmark",
    "laptop",
    "library",
    "list",
    "lock-keyhole",
    "mail",
    "map",
    "map-pin",
    "message-square",
    "microscope",
    "moon",
    "music-2",
    "pencil",
    "pencil-line",
    "pill",
    "plane",
    "plus",
    "rows-3",
    "scan-qr-code",
    "search",
    "send",
    "settings-2",
    "shield",
    "shield-alert",
    "shield-check",
    "shopping-bag",
    "shopping-cart",
    "smartphone",
    "star",
    "stethoscope",
    "store",
    "sun",
    "target",
    "train-front",
    "trash-2",
    "triangle-alert",
    "trophy",
    "tv",
    "upload",
    "user-round",
    "users-round",
    "vault",
    "wallet-cards",
    "x",
    "zap",
})

ICON_ALIASES = {
    "all_accounts": "rows-3",
    "arrow_left": "arrow-left",
    "bank": "landmark",
    "bolt": "zap",
    "book": "book-open",
    "briefcase": "briefcase-business",
    "building": "building-2",
    "car": "car-front",
    "card": "credit-card",
    "cart": "shopping-cart",
    "chart": "chart-no-axes-column-increasing",
    "check": "circle-check",
    "chevron": "chevron-right",
    "close": "x",
    "diamond": "gem",
    "device": "smartphone",
    "education": "graduation-cap",
    "edit": "pencil-line",
    "error": "circle-x",
    "film": "clapperboard",
    "game": "gamepad-2",
    "health": "heart-pulse",
    "home": "house",
    "key": "key-round",
    "lock": "lock-keyhole",
    "message": "message-square",
    "music": "music-2",
    "science": "flask-conical",
    "shield_check": "shield-check",
    "totp": "scan-qr-code",
    "train": "train-front",
    "trash": "trash-2",
    "users": "users-round",
    "vault": "vault",
    "warning": "triangle-alert",
}

LEGACY_ICON_NAMES = {
    "📱": "smartphone",
    "💬": "message-square",
    "📸": "camera",
    "🐦": "bird",
    "👥": "users-round",
    "💌": "mail",
    "📧": "mail",
    "✉️": "mail",
    "📨": "inbox",
    "📮": "send",
    "🏦": "landmark",
    "💳": "credit-card",
    "💰": "wallet-cards",
    "💵": "banknote",
    "📈": "chart-no-axes-column-increasing",
    "🛒": "shopping-cart",
    "🛍️": "shopping-bag",
    "🏪": "store",
    "🎁": "gift",
    "💎": "gem",
    "🎮": "gamepad-2",
    "🕹️": "gamepad-2",
    "🎯": "target",
    "🏆": "trophy",
    "🎲": "dice-5",
    "💼": "briefcase-business",
    "🏢": "building-2",
    "📊": "chart-pie",
    "📋": "clipboard-list",
    "💻": "laptop",
    "🎬": "clapperboard",
    "🎵": "music-2",
    "📺": "tv",
    "🎧": "headphones",
    "📖": "book-open",
    "✈️": "plane",
    "🚗": "car-front",
    "🏨": "hotel",
    "🗺️": "map",
    "🚆": "train-front",
    "🏥": "hospital",
    "💊": "pill",
    "🩺": "stethoscope",
    "❤️": "heart",
    "🏃": "activity",
    "🎓": "graduation-cap",
    "📚": "library",
    "🔬": "microscope",
    "🧪": "flask-conical",
    "✏️": "pencil",
    "🔑": "key-round",
    "🌐": "globe",
    "⭐": "star",
    "🔧": "settings-2",
    "🏠": "house",
    "🔒": "lock-keyhole",
    "📁": "folder",
    "☁️": "cloud",
    "🛡️": "shield",
    "⚡": "zap",
}


def normalize_icon(name: str) -> str:
    """Resolve current Lucide names and legacy category values to one icon."""
    if name in LEGACY_ICON_NAMES:
        return LEGACY_ICON_NAMES[name]
    normalized = ICON_ALIASES.get(name, name)
    return normalized if normalized in ICON_NAMES else "folder"


def _resolve_color(value):
    if isinstance(value, (tuple, list)):
        return value[1 if theme.is_dark() else 0]
    if value in {
        "accent",
        "accent_glow",
        "accent_light",
        "bg_active",
        "bg_card",
        "bg_dialog",
        "bg_hover",
        "bg_input",
        "bg_primary",
        "bg_secondary",
        "bg_tertiary",
        "border",
        "border_focus",
        "border_light",
        "error",
        "error_light",
        "info",
        "scrollbar",
        "scrollbar_hover",
        "success",
        "text_muted",
        "text_on_accent",
        "text_primary",
        "text_secondary",
        "warning",
    }:
        return theme.get(value)[1 if theme.is_dark() else 0]
    return value


@lru_cache(maxsize=96)
def _load_alpha_mask(icon_name: str):
    icon_path = _RASTER_ROOT / f"{icon_name}.png"
    if not icon_path.is_file():
        raise FileNotFoundError(f"Lucide icon resource is missing: {icon_path}")
    with Image.open(icon_path) as source:
        return source.convert("RGBA").getchannel("A")


@lru_cache(maxsize=512)
def _tinted_image(icon_name: str, color: str, size: int):
    mask = _load_alpha_mask(icon_name)
    if mask.size != (size, size):
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    image = Image.new("RGBA", (size, size), ImageColor.getrgb(color))
    image.putalpha(mask)
    return image


@lru_cache(maxsize=512)
def _customtkinter_image(icon_name: str, color: str, size: int):
    image = _tinted_image(icon_name, color, size)
    return ctk.CTkImage(
        light_image=image,
        dark_image=image,
        size=(size, size),
    )


class Icon(ctk.CTkLabel):
    """Display a color-tinted, high-resolution Lucide icon resource."""

    def __init__(
        self,
        parent,
        name: str,
        size: int = 18,
        color="text_secondary",
        background="bg_secondary",
        **kwargs,
    ):
        self.name = normalize_icon(name)
        self.size = size
        self.color = color
        self.background = background
        if size <= 0:
            raise ValueError("Icon size must be greater than zero.")
        self._icon_image = _customtkinter_image(
            self.name, str(_resolve_color(color)), size
        )
        super().__init__(
            parent,
            text="",
            image=self._icon_image,
            width=size,
            height=size,
            fg_color="transparent",
            corner_radius=0,
            **kwargs,
        )

    def refresh(self):
        self.name = normalize_icon(self.name)
        image = _customtkinter_image(
            self.name, str(_resolve_color(self.color)), self.size
        )
        if image is not self._icon_image:
            self._icon_image = image
            self.configure(image=image)

    def draw(self):
        self.refresh()


class IconButton:
    """Attach a centered Lucide icon to a keyboard-accessible CTkButton."""

    def __init__(
        self,
        parent,
        name: str,
        command,
        size: int = 18,
        color="text_secondary",
        background="transparent",
        hover_background="bg_hover",
        **button_options,
    ):
        if background == "transparent":
            background = "bg_secondary"
        self.button = ctk.CTkButton(parent, text="", command=command, **button_options)
        self.icon = Icon(
            self.button,
            name,
            size=size,
            color=color,
            background=background,
        )
        self.icon.place(relx=0.5, rely=0.5, anchor="center")
        self._background = background
        self._hover_background = hover_background
        self._tooltip_after_id = None
        self._tooltip_window = None
        self.button.bind("<Enter>", self._on_enter, add="+")
        self.button.bind("<Leave>", self._on_leave, add="+")
        self.button.bind("<FocusIn>", self._on_enter, add="+")
        self.button.bind("<FocusOut>", self._on_leave, add="+")
        self.button.bind("<Destroy>", self._on_destroy, add="+")
        self.icon.bind("<Button-1>", lambda _event: self.button.invoke())
        self.icon.bind("<Enter>", self._on_enter)
        self.icon.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event=None):
        self.icon.background = self._hover_background
        self._cancel_tooltip()
        if getattr(self.button, "accessible_name", ""):
            self._tooltip_after_id = self.button.after(550, self._show_tooltip)

    def _on_leave(self, _event=None):
        self.icon.background = self._background
        self._cancel_tooltip()
        self._hide_tooltip()

    def _cancel_tooltip(self):
        if self._tooltip_after_id is not None:
            self.button.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = None

    def _show_tooltip(self):
        self._tooltip_after_id = None
        label = getattr(self.button, "accessible_name", "")
        if not label or not self.button.winfo_exists():
            return

        tooltip = ctk.CTkToplevel(self.button)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        tooltip.attributes("-topmost", True)
        tooltip.configure(
            fg_color=theme.get("bg_tertiary"),
            border_width=1,
            border_color=theme.get("border_light"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
        )
        ctk.CTkLabel(
            tooltip,
            text=label,
            font=FONTS["caption"],
            text_color=theme.get("text_primary"),
        ).pack(padx=8, pady=5)
        tooltip.update_idletasks()

        x = self.button.winfo_rootx() + self.button.winfo_width() // 2
        x -= tooltip.winfo_width() // 2
        x = max(4, min(x, tooltip.winfo_screenwidth() - tooltip.winfo_width() - 4))
        y = self.button.winfo_rooty() + self.button.winfo_height() + 5
        if y + tooltip.winfo_height() > tooltip.winfo_screenheight() - 4:
            y = self.button.winfo_rooty() - tooltip.winfo_height() - 5
        tooltip.geometry(f"+{x}+{max(4, y)}")
        tooltip.deiconify()
        self._tooltip_window = tooltip

    def _hide_tooltip(self):
        if self._tooltip_window is not None:
            if self._tooltip_window.winfo_exists():
                self._tooltip_window.destroy()
            self._tooltip_window = None

    def _on_destroy(self, event):
        if event.widget is self.button:
            self._cancel_tooltip()
            self._hide_tooltip()

    def pack(self, **kwargs):
        self.button.pack(**kwargs)
        return self

    def grid(self, **kwargs):
        self.button.grid(**kwargs)
        return self

    def place(self, **kwargs):
        self.button.place(**kwargs)
        return self


def refresh_icons(root):
    for child in root.winfo_children():
        if isinstance(child, Icon):
            child.refresh()
        refresh_icons(child)
