import customtkinter as ctk
from src.ui.theme import theme, FONTS, DIMENSIONS, button_style
from src.ui.icons import Icon


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
            fg_color=theme.get("bg_card"),
            corner_radius=DIMENSIONS["corner_radius_lg"],
            border_width=1,
            border_color=theme.get("border"),
            width=380,
            height=350,
        )
        card.grid_propagate(False)
        card.grid(row=1, column=0, padx=40, pady=40)
        card.grid_columnconfigure(0, weight=1)

        logo = ctk.CTkFrame(
            card,
            fg_color=theme.get("accent_light"),
            corner_radius=18,
            width=72,
            height=72,
        )
        logo.grid(row=0, column=0, pady=(36, 18))
        logo.grid_propagate(False)
        Icon(
            logo,
            "lock",
            size=34,
            color="accent",
            background="accent_light",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text="Application verrouillée",
            font=FONTS["heading"],
            text_color=theme.get("text_primary"),
        ).grid(row=1, column=0, pady=(0, 8))

        ctk.CTkLabel(
            card,
            text="Ta session a expiré après une période d’inactivité.",
            font=FONTS["body"],
            text_color=theme.get("text_secondary"),
            width=300,
            wraplength=280,
            justify="center",
        ).grid(row=2, column=0, pady=(0, 26))

        ctk.CTkButton(
            card,
            text="Déverrouiller mon coffre",
            font=FONTS["body_bold"],
            width=270,
            **button_style("primary", height=46),
            command=self._go_login,
        ).grid(row=3, column=0, pady=(0, 14))

        ctk.CTkLabel(
            card,
            text="Tes données restent chiffrées pendant le verrouillage.",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
        ).grid(row=4, column=0, pady=(0, 38))

    def _go_login(self):
        if self.on_unlock:
            self.on_unlock()