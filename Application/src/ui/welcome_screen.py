import tkinter as tk

import customtkinter as ctk

from src.ui.theme import DIMENSIONS, FONTS, theme


class VaultIllustration(tk.Canvas):
    """A lightweight, pointer-responsive isometric illustration of the vault."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            width=360,
            height=230,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._pointer = (0.0, 0.0)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._draw)
        self._draw()

    def _on_motion(self, event):
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        self._pointer = (
            (event.x / width - 0.5) * 8,
            (event.y / height - 0.5) * 5,
        )
        self._draw()

    def _on_leave(self, _event=None):
        self._pointer = (0.0, 0.0)
        self._draw()

    def _draw(self, _event=None):
        if not self.winfo_exists():
            return
        mode_index = 1 if theme.is_dark() else 0

        def color(token):
            value = theme.get(token)
            return value[mode_index] if isinstance(value, tuple) else value

        self.configure(bg=color("bg_primary"))
        self.delete("all")
        width = max(self.winfo_width(), 360)
        height = max(self.winfo_height(), 230)
        dx, dy = self._pointer
        ox = (width - 360) / 2
        oy = (height - 230) / 2

        def points(values, depth=1.0):
            return [
                coordinate
                for index in range(0, len(values), 2)
                for coordinate in (
                    ox + values[index] + dx * depth,
                    oy + values[index + 1] + dy * depth,
                )
            ]

        self.create_polygon(
            *points((42, 151, 164, 198, 315, 141, 191, 97), 0.35),
            fill=color("accent_light"),
            outline="",
        )
        self.create_polygon(
            *points((49, 128, 164, 174, 164, 198, 49, 153), 0.65),
            fill=color("bg_tertiary"),
            outline="",
        )
        self.create_polygon(
            *points((164, 174, 293, 124, 293, 149, 164, 198), 0.85),
            fill=color("border"),
            outline="",
        )
        self.create_polygon(
            *points((49, 128, 178, 79, 293, 124, 164, 174), 1.0),
            fill=color("bg_card"),
            outline=color("border"),
            width=1,
        )

        cx = ox + 171 + dx
        cy = oy + 125 + dy
        self.create_oval(
            cx - 41,
            cy - 27,
            cx + 41,
            cy + 27,
            fill=color("accent_light"),
            outline=color("border_light"),
            width=1,
        )
        self.create_oval(
            cx - 30,
            cy - 20,
            cx + 30,
            cy + 20,
            fill=color("bg_secondary"),
            outline=color("accent"),
            width=3,
        )
        for dx, dy in ((0, -25), (25, 0), (0, 25), (-25, 0)):
            self.create_oval(
                cx + dx - 2,
                cy + dy - 2,
                cx + dx + 2,
                cy + dy + 2,
                fill=color("border_light"),
                outline="",
            )
        self.create_oval(
            cx - 7,
            cy - 7,
            cx + 7,
            cy + 7,
            fill=color("accent"),
            outline="",
        )
        self.create_polygon(
            cx - 4,
            cy + 4,
            cx + 4,
            cy + 4,
            cx + 6,
            cy + 14,
            cx - 6,
            cy + 14,
            fill=color("accent"),
            outline="",
        )


class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, parent, on_continue=None, **kwargs):
        super().__init__(parent, fg_color=theme.get("bg_primary"), **kwargs)
        self.on_continue = on_continue
        self._build()

    def _build(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        self.illustration = VaultIllustration(content)
        self.illustration.pack(pady=(0, 12))

        ctk.CTkLabel(
            content,
            text="VaultApp",
            font=FONTS["heading_xl"],
            text_color=theme.get("text_primary"),
        ).pack()
        ctk.CTkLabel(
            content,
            text="Vos accès. En sécurité. Tout simplement.",
            font=FONTS["body_lg"],
            text_color=theme.get("text_secondary"),
        ).pack(pady=(8, 26))
        ctk.CTkButton(
            content,
            text="Continuer",
            font=FONTS["body_bold"],
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text_on_accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=46,
            width=220,
            command=self._go,
        ).pack()
        ctk.CTkLabel(
            content,
            text="Privé par conception · Chiffré sur cet appareil",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
        ).pack(pady=(18, 0))

    def _go(self):
        if self.on_continue:
            self.on_continue()
