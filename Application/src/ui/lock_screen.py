import customtkinter as ctk
from src.ui.theme import theme, FONTS, DIMENSIONS


class LockScreen(ctk.CTkFrame):

    def __init__(self, parent, on_unlock=None, **kwargs):
        super().__init__(parent, fg_color=theme.get("bg_primary"), **kwargs)
        self.on_unlock = on_unlock
        self._build()

    def _build(self):
        # Centrage vertical
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
            card, text="🔒",
            font=("Segoe UI", 64),
        ).grid(row=0, column=0, pady=(48, 8))

        ctk.CTkLabel(
            card,
            text="Application verrouillée",
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
        ).grid(row=1, column=0, pady=(0, 8))

        ctk.CTkLabel(
            card,
            text="La session a expiré par inactivité.",
            font=FONTS["body"],
            text_color=theme.get("text_secondary"),
        ).grid(row=2, column=0, pady=(0, 32))

        ctk.CTkButton(
            card,
            text="🔓  Se reconnecter",
            font=FONTS["body_bold"],
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text_on_accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["button_height"],
            width=220,
            command=self._go_login,
        ).grid(row=3, column=0, pady=(0, 48))

    def _go_login(self):
        if self.on_unlock:
            self.on_unlock()