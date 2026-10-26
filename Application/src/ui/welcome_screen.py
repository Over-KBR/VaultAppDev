import customtkinter as ctk
from src.ui.theme import theme, FONTS, DIMENSIONS


class WelcomeScreen(ctk.CTkFrame):

    def __init__(self, parent, on_continue=None, **kwargs):
        super().__init__(parent, fg_color=theme.get("bg_primary"), **kwargs)
        self.on_continue = on_continue
        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            fg_color=theme.get("bg_secondary"),
            corner_radius=24,
            border_width=1,
            border_color=theme.get("border"),
        )
        card.grid(row=1, column=0, padx=40, pady=40, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="🔐",
            font=("Segoe UI", 72),
        ).grid(row=0, column=0, pady=(52, 8))

        ctk.CTkLabel(
            card,
            text="Bonjour 👋",
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
        ).grid(row=1, column=0, pady=(0, 10))

        ctk.CTkLabel(
            card,
            text="Bienvenue sur VaultApp\nTous vos mots de passe, en sécurité.",
            font=FONTS["body"],
            text_color=theme.get("text_secondary"),
            justify="center",
        ).grid(row=2, column=0, pady=(0, 36))

        ctk.CTkButton(
            card,
            text="🔓  Se connecter",
            font=FONTS["body_bold"],
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text_on_accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["button_height"],
            width=220,
            command=self._go,
        ).grid(row=3, column=0, pady=(0, 52))

    def _go(self):
        if self.on_continue:
            self.on_continue()