"""Small, consistent vector icons for the CustomTkinter interface."""

import math
import tkinter as tk

import customtkinter as ctk

from src.ui.theme import theme


LEGACY_ICON_NAMES = {
    "📱": "device", "💬": "message", "📸": "camera", "🐦": "bird",
    "👥": "users", "💌": "mail", "📧": "mail", "✉️": "mail",
    "📨": "mail", "📮": "mail", "🏦": "bank", "💳": "card",
    "💰": "bank", "💵": "bank", "📈": "chart", "🛒": "cart",
    "🛍️": "cart", "🏪": "store", "🎁": "gift", "💎": "diamond",
    "🎮": "game", "🕹️": "game", "🎯": "target", "🏆": "award",
    "🎲": "dice", "💼": "briefcase", "🏢": "building", "📊": "chart",
    "📋": "list", "💻": "device", "🎬": "film", "🎵": "music",
    "📺": "device", "🎧": "headphones", "📖": "book", "✈️": "plane",
    "🚗": "car", "🏨": "building", "🗺️": "map", "🚆": "train",
    "🏥": "health", "💊": "health", "🩺": "health", "❤️": "heart",
    "🏃": "activity", "🎓": "education", "📚": "book", "🔬": "science",
    "🧪": "science", "✏️": "edit", "🔑": "key", "🌐": "globe",
    "⭐": "star", "🔧": "settings", "🏠": "home", "🔒": "lock",
    "📁": "folder", "☁️": "cloud", "🛡️": "shield", "⚡": "bolt",
}


def normalize_icon(name: str) -> str:
    return LEGACY_ICON_NAMES.get(name, name if name in ICON_NAMES else "folder")


ICON_NAMES = {
    "search", "list", "star", "shield", "shield_check", "settings",
    "sun", "moon", "plus", "folder", "lock", "key", "user", "users",
    "copy", "edit", "trash", "eye", "eye_off", "totp", "check",
    "warning", "error", "info", "upload", "download", "dice", "close",
    "vault",
    "arrow_left", "chevron", "device", "message", "camera", "bird",
    "mail", "bank", "card", "chart", "cart", "store", "gift",
    "diamond", "game", "target", "award", "briefcase", "building",
    "film", "music", "headphones", "book", "plane", "car", "train",
    "health", "heart", "activity", "education", "science", "globe",
    "home", "cloud", "bolt", "map",
}


def _color(value):
    if isinstance(value, (tuple, list)):
        return value[0 if not theme.is_dark() else 1]
    if value in {"bg_primary", "bg_secondary", "bg_tertiary", "bg_card", "bg_dialog",
                 "bg_input", "bg_hover", "bg_active",
                 "accent", "accent_light", "accent_glow", "text_primary",
                 "text_secondary", "text_muted", "text_on_accent", "border", "border_light",
                 "border_focus", "success", "warning", "error", "error_light", "info",
                 "scrollbar", "scrollbar_hover", "shadow"}:
        return theme.get(value)[1 if theme.is_dark() else 0]
    return value


class Icon(tk.Canvas):
    """A compact outline icon drawn on a native canvas."""

    def __init__(
        self,
        parent,
        name: str,
        size: int = 18,
        color="text_secondary",
        background="bg_secondary",
        stroke_width: float = 1.8,
        **kwargs,
    ):
        self.name = normalize_icon(name)
        self.size = size
        self.color = color
        self.background = background
        self.stroke_width = stroke_width
        super().__init__(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            relief="flat",
            bg=_color(background),
            **kwargs,
        )
        self.draw()

    def refresh(self):
        self.configure(bg=_color(self.background))
        self.draw()

    def _xy(self, value):
        return value * self.size / 24

    def _line(self, *coordinates, width=None, smooth=False):
        self.create_line(
            *(self._xy(point) for point in coordinates),
            fill=_color(self.color),
            width=width or self.stroke_width,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            smooth=smooth,
        )

    def _oval(self, x1, y1, x2, y2, fill="", width=None):
        self.create_oval(
            *(self._xy(point) for point in (x1, y1, x2, y2)),
            outline=_color(self.color),
            fill=fill,
            width=width or self.stroke_width,
        )

    def _rect(self, x1, y1, x2, y2, radius=3):
        scale = self.size / 24
        self.create_rectangle(
            x1 * scale, y1 * scale, x2 * scale, y2 * scale,
            outline=_color(self.color), width=self.stroke_width,
        )

    def _poly(self, *coordinates, fill=""):
        self.create_polygon(
            *(self._xy(point) for point in coordinates),
            outline=_color(self.color),
            fill=fill,
            width=self.stroke_width,
            joinstyle=tk.ROUND,
        )

    def draw(self):
        if not self.winfo_exists():
            return
        self.delete("all")
        n = self.name
        if n == "search":
            self._oval(3, 3, 15, 15)
            self._line(13.5, 13.5, 21, 21)
        elif n in {"list", "menu"}:
            for y in (5, 12, 19):
                self._line(4, y, 20, y)
        elif n == "star":
            points = []
            for index in range(10):
                angle = -math.pi / 2 + index * math.pi / 5
                radius = 9 if index % 2 == 0 else 4
                points.extend((12 + math.cos(angle) * radius, 12 + math.sin(angle) * radius))
            self._poly(*points)
        elif n in {"shield", "shield_check"}:
            self._poly(12, 2, 20, 5, 19, 13, 16, 18, 12, 22, 8, 18, 5, 13, 4, 5, 12, 2)
            if n == "shield_check":
                self._line(8, 12, 11, 15, 16, 9)
        elif n == "settings":
            self._oval(8, 8, 16, 16)
            self._oval(10, 10, 14, 14)
            for x1, y1, x2, y2 in (
                (12, 2, 12, 6), (12, 18, 12, 22), (2, 12, 6, 12),
                (18, 12, 22, 12), (5, 5, 8, 8), (16, 16, 19, 19),
                (5, 19, 8, 16), (16, 8, 19, 5),
            ):
                self._line(x1, y1, x2, y2)
        elif n in {"sun", "moon"}:
            if n == "sun":
                self._oval(8, 8, 16, 16)
                for x1, y1, x2, y2 in (
                    (12, 2, 12, 5), (12, 19, 12, 22), (2, 12, 5, 12),
                    (19, 12, 22, 12), (5, 5, 7, 7), (17, 17, 19, 19),
                    (5, 19, 7, 17), (17, 7, 19, 5),
                ):
                    self._line(x1, y1, x2, y2)
            else:
                self._oval(5, 3, 20, 21)
                self.create_oval(
                    self._xy(11), self._xy(1), self._xy(24), self._xy(17),
                    fill=_color(self.background), outline=_color(self.background),
                )
        elif n == "plus":
            self._line(12, 4, 12, 20)
            self._line(4, 12, 20, 12)
        elif n == "folder":
            self._line(3, 6, 10, 6, 12, 9, 21, 9, 20, 19, 4, 19, 3, 6)
        elif n == "vault":
            self._rect(3, 3, 21, 21)
            self._oval(7, 7, 17, 17)
            self._oval(10, 10, 14, 14)
            self._line(12, 4, 12, 7)
            self._line(12, 17, 12, 20)
            self._line(4, 12, 7, 12)
            self._line(17, 12, 20, 12)
        elif n == "lock":
            self._rect(4, 10, 20, 21)
            self._line(7, 10, 7, 7, 9, 4, 12, 3, 15, 4, 17, 7, 17, 10)
            self._oval(11, 13, 13, 15)
            self._line(12, 15, 12, 18)
        elif n == "key":
            self._oval(3, 6, 14, 17)
            self._line(12, 15, 21, 21)
            self._line(17, 18, 19, 16)
            self._line(19, 20, 21, 18)
        elif n in {"user", "users"}:
            self._oval(8, 3, 16, 11)
            self._line(4, 21, 5, 17, 8, 14, 12, 13, 16, 14, 19, 17, 20, 21)
            if n == "users":
                self._line(3, 8, 4, 5, 7, 4)
                self._line(21, 8, 20, 5, 17, 4)
        elif n == "copy":
            self._rect(8, 7, 20, 21)
            self._line(5, 17, 4, 17, 4, 3, 16, 3, 16, 5)
        elif n == "edit":
            self._line(4, 17, 3, 21, 7, 20, 19, 8, 16, 5, 4, 17)
            self._line(14, 7, 17, 10)
        elif n == "trash":
            self._line(4, 6, 20, 6)
            self._line(9, 3, 15, 3)
            self._line(6, 7, 7, 21, 17, 21, 18, 7)
            self._line(10, 10, 10, 18)
            self._line(14, 10, 14, 18)
        elif n in {"eye", "eye_off"}:
            self._poly(2, 12, 5, 8, 9, 5, 12, 4, 15, 5, 19, 8, 22, 12, 19, 16, 15, 19, 12, 20, 9, 19, 5, 16, 2, 12)
            self._oval(9, 9, 15, 15)
            if n == "eye_off":
                self._line(4, 4, 20, 20)
        elif n == "totp":
            for x, y in ((7, 7), (12, 7), (17, 7), (7, 12), (12, 12), (17, 12), (7, 17), (12, 17), (17, 17)):
                self.create_oval(self._xy(x-1), self._xy(y-1), self._xy(x+1), self._xy(y+1), fill=_color(self.color), outline="")
        elif n == "check":
            self._oval(2, 2, 22, 22)
            self._line(7, 12, 10, 15, 17, 8)
        elif n == "warning":
            self._poly(12, 3, 22, 21, 2, 21, 12, 3)
            self._line(12, 9, 12, 14)
            self._oval(11.3, 17, 12.7, 18.4, fill=_color(self.color), width=0)
        elif n == "error":
            self._oval(2, 2, 22, 22)
            self._line(8, 8, 16, 16)
            self._line(16, 8, 8, 16)
        elif n == "info":
            self._oval(2, 2, 22, 22)
            self._line(12, 11, 12, 17)
            self._oval(11.2, 6.5, 12.8, 8.1, fill=_color(self.color), width=0)
        elif n in {"upload", "download"}:
            if n == "upload":
                self._line(12, 17, 12, 4, 7, 9)
                self._line(12, 4, 17, 9)
                self._line(4, 18, 4, 21, 20, 21, 20, 18)
            else:
                self._line(12, 4, 12, 17, 7, 12)
                self._line(12, 17, 17, 12)
                self._line(4, 18, 4, 21, 20, 21, 20, 18)
        elif n == "dice":
            self._rect(3, 3, 21, 21)
            for x, y in ((7, 7), (17, 7), (12, 12), (7, 17), (17, 17)):
                self.create_oval(self._xy(x-1), self._xy(y-1), self._xy(x+1), self._xy(y+1), fill=_color(self.color), outline="")
        elif n == "close":
            self._line(5, 5, 19, 19)
            self._line(19, 5, 5, 19)
        elif n in {"arrow_left", "chevron"}:
            self._line(14, 5, 7, 12, 14, 19)
            if n == "arrow_left":
                self._line(7, 12, 21, 12)
        elif n == "device":
            self._rect(5, 2, 19, 22)
            self._line(9, 5, 15, 5)
            self._oval(11, 18, 13, 20)
        elif n == "camera":
            self._rect(3, 7, 21, 20)
            self._oval(8, 10, 16, 18)
            self._line(7, 7, 9, 4, 15, 4, 17, 7)
        elif n == "bird":
            self._oval(11, 3, 18, 10)
            self._oval(5, 9, 18, 18)
            self._line(17, 5, 22, 7, 17, 9)
            self._line(7, 13, 11, 11, 16, 13, 11, 16, 7, 13)
            self._line(6, 13, 3, 11)
            self._line(6, 15, 3, 17)
            self._line(10, 18, 9, 21, 12, 21)
            self._line(15, 18, 16, 21, 19, 21)
            self._oval(14, 5, 15.5, 6.5, fill=_color(self.color), width=0)
        elif n == "mail":
            self._rect(3, 5, 21, 19)
            self._line(4, 7, 12, 13, 20, 7)
        elif n == "message":
            self._line(5, 5, 19, 5, 21, 7, 21, 16, 19, 18, 10, 18, 5, 22, 6, 18, 3, 16, 3, 7, 5, 5)
            self._line(7, 10, 17, 10)
            self._line(7, 14, 14, 14)
        elif n == "bank":
            self._poly(3, 9, 12, 3, 21, 9, 3, 9)
            self._line(4, 20, 20, 20)
            self._line(3, 22, 21, 22)
            for x in (7, 12, 17):
                self._line(x, 10, x, 19)
        elif n == "card":
            self._rect(3, 5, 21, 19)
            self._line(4, 10, 20, 10)
            self._line(7, 15, 11, 15)
        elif n == "chart":
            self._line(3, 20, 3, 4)
            self._line(3, 20, 21, 20)
            self._line(6, 16, 10, 12, 14, 15, 20, 7)
        elif n == "cart":
            self._line(3, 4, 6, 5, 8, 16, 19, 16, 21, 8, 7, 8)
            self._oval(8, 18, 10, 20)
            self._oval(17, 18, 19, 20)
        elif n == "store":
            self._line(4, 10, 5, 4, 19, 4, 20, 10)
            self._line(4, 10, 4, 20, 20, 20, 20, 10)
            self._line(4, 10, 7, 12, 10, 10, 12, 12, 15, 10, 17, 12, 20, 10)
            self._rect(8, 14, 12, 20)
        elif n == "gift":
            self._rect(4, 10, 20, 21)
            self._line(3, 8, 21, 8)
            self._line(12, 8, 12, 21)
            self._line(12, 8, 8, 7, 7, 4, 9, 3, 12, 8, 15, 3, 17, 4, 16, 7, 12, 8)
        elif n == "diamond":
            self._poly(3, 8, 7, 3, 17, 3, 21, 8, 12, 21, 3, 8)
            self._line(3, 8, 21, 8)
            self._line(7, 3, 9, 8, 12, 21)
            self._line(17, 3, 15, 8, 12, 21)
        elif n == "game":
            self._line(7, 7, 17, 7, 20, 10, 21, 16, 19, 19, 16, 18, 13, 15, 11, 15, 8, 18, 5, 19, 3, 16, 4, 10, 7, 7)
            self._line(7, 10, 7, 15)
            self._line(4.5, 12.5, 9.5, 12.5)
            self._oval(15, 10, 16, 11, fill=_color(self.color), width=0)
            self._oval(17, 13, 18, 14, fill=_color(self.color), width=0)
        elif n == "target":
            self._oval(3, 3, 21, 21)
            self._oval(7, 7, 17, 17)
            self._oval(10, 10, 14, 14)
            self._line(13, 11, 21, 3, 17, 3)
            self._line(21, 3, 21, 7)
        elif n == "award":
            self._poly(6, 4, 9, 6, 12, 4, 15, 6, 18, 4, 19, 11, 17, 16, 12, 19, 7, 16, 5, 11, 6, 4)
            self._poly(8, 16, 7, 22, 12, 19, 17, 22, 16, 16)
            self._line(9, 11, 11, 13, 15, 9)
        elif n == "briefcase":
            self._rect(3, 8, 21, 20)
            self._line(9, 8, 9, 5, 15, 5, 15, 8)
            self._line(3, 12, 21, 12)
            self._line(10, 12, 10, 14, 14, 14, 14, 12)
        elif n == "building":
            self._rect(5, 3, 19, 21)
            for x in (9, 15):
                for y in (7, 12, 17):
                    self._rect(x - 1, y - 1, x + 1, y + 1)
        elif n == "film":
            self._rect(3, 5, 21, 19)
            self._line(7, 5, 7, 19)
            self._line(17, 5, 17, 19)
            self._line(3, 9, 7, 9)
            self._line(17, 9, 21, 9)
            self._line(3, 15, 7, 15)
            self._line(17, 15, 21, 15)
            self._poly(10, 9, 16, 12, 10, 15, 10, 9)
        elif n == "music":
            self._line(14, 5, 14, 17, 20, 15, 20, 3, 14, 5)
            self._oval(7, 16, 14, 21)
        elif n == "headphones":
            self._line(4, 13, 4, 10, 6, 6, 9, 4, 12, 3, 15, 4, 18, 6, 20, 10, 20, 13)
            self._line(4, 12, 4, 19, 8, 19, 8, 13, 4, 13)
            self._line(20, 12, 20, 19, 16, 19, 16, 13, 20, 13)
        elif n == "book":
            self._poly(3, 5, 9, 4, 12, 6, 15, 4, 21, 5, 21, 20, 15, 19, 12, 21, 9, 19, 3, 20, 3, 5)
            self._line(12, 6, 12, 21)
            self._line(5, 8, 9, 7)
            self._line(15, 7, 19, 8)
        elif n == "plane":
            self._poly(3, 11, 21, 3, 15, 21, 11, 14, 3, 11)
            self._line(11, 14, 21, 3)
            self._line(11, 14, 12, 20)
        elif n == "car":
            self._line(3, 15, 5, 9, 8, 7, 17, 7, 20, 11, 21, 15, 21, 18, 3, 18, 3, 15)
            self._line(7, 9, 8, 13, 17, 13, 18, 10)
            self._oval(6, 16, 10, 20)
            self._oval(15, 16, 19, 20)
        elif n == "train":
            self._rect(5, 3, 19, 19)
            self._line(8, 7, 16, 7)
            self._line(7, 12, 9, 14, 11, 12)
            self._line(13, 12, 15, 14, 17, 12)
            self._line(8, 19, 5, 22)
            self._line(16, 19, 19, 22)
        elif n == "map":
            self._poly(3, 5, 9, 3, 15, 5, 21, 3, 21, 19, 15, 21, 9, 19, 3, 21, 3, 5)
            self._line(9, 3, 9, 19)
            self._line(15, 5, 15, 21)
            self._line(5, 8, 7, 7)
            self._line(17, 9, 19, 8)
        elif n == "health":
            self._rect(4, 4, 20, 20)
            self._line(12, 8, 12, 16)
            self._line(8, 12, 16, 12)
        elif n == "heart":
            self._poly(12, 21, 4, 13, 3, 8, 5, 5, 9, 5, 12, 9, 15, 5, 19, 5, 21, 8, 20, 13, 12, 21)
        elif n == "activity":
            self._line(2, 13, 7, 13, 10, 7, 14, 18, 17, 12, 22, 12)
        elif n == "education":
            self._poly(2, 9, 12, 4, 22, 9, 12, 14, 2, 9)
            self._line(6, 11, 6, 17, 12, 20, 18, 17, 18, 11)
            self._line(21, 10, 21, 16)
        elif n == "science":
            self._line(9, 3, 15, 3)
            self._line(10, 3, 10, 10, 5, 19, 6, 21, 18, 21, 19, 19, 14, 10, 14, 3)
            self._line(7, 16, 17, 16)
            self._oval(9, 17, 10, 18, fill=_color(self.color), width=0)
            self._oval(14, 18, 15, 19, fill=_color(self.color), width=0)
        elif n == "globe":
            self._oval(3, 3, 21, 21)
            self._oval(8, 3, 16, 21)
            self._line(4, 9, 20, 9)
            self._line(4, 15, 20, 15)
        elif n == "home":
            self._poly(3, 11, 12, 3, 21, 11, 19, 11, 19, 21, 5, 21, 5, 11, 3, 11)
            self._rect(10, 14, 14, 21)
        elif n == "cloud":
            self._line(6, 18, 4, 16, 4, 13, 6, 11, 9, 11, 10, 7, 13, 5, 17, 7, 18, 11, 21, 12, 21, 16, 19, 18, 6, 18)
        elif n == "bolt":
            self._poly(13, 2, 5, 13, 11, 13, 9, 22, 19, 10, 13, 10, 13, 2)
        elif n == "totp":
            for x, y in ((7, 7), (12, 7), (17, 7), (7, 12), (12, 12), (17, 12), (7, 17), (12, 17), (17, 17)):
                self.create_oval(self._xy(x-1), self._xy(y-1), self._xy(x+1), self._xy(y+1), fill=_color(self.color), outline="")


class IconButton:
    """Attach a crisp vector icon to a real, keyboard-operable CTkButton."""

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
        self.button.bind("<Enter>", self._on_enter, add="+")
        self.button.bind("<Leave>", self._on_leave, add="+")
        self.icon.bind("<Button-1>", lambda _event: self.button.invoke())
        self.icon.bind("<Enter>", self._on_enter)
        self.icon.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event=None):
        self.icon.background = self._hover_background
        self.icon.refresh()

    def _on_leave(self, _event=None):
        self.icon.background = self._background
        self.icon.refresh()

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
