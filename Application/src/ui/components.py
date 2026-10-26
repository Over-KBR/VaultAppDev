"""
Composants UI réutilisables pour VaultApp.

Ces widgets sont les "briques" de l'interface :
- SearchBar : barre de recherche avec icône
- AccountCard : carte affichant un compte
- CategoryButton : bouton de catégorie dans la sidebar
- IconButton : petit bouton avec icône
- ToastNotification : notification temporaire
"""

import customtkinter as ctk
from src.ui.theme import (
    theme,
    FONTS,
    DIMENSIONS,
    MOTION,
    blend_colors,
)
from src.ui.icons import Icon, IconButton, normalize_icon


class SearchBar(ctk.CTkFrame):
    """Barre de recherche avec icône loupe et bouton effacer."""
    
    def __init__(self, parent, on_search=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.on_search = on_search
        self._search_focused = False
        
        # Conteneur de la barre
        self.search_frame = ctk.CTkFrame(
            self,
            fg_color=theme.get("bg_input"),
            corner_radius=DIMENSIONS["corner_radius_lg"],
            border_width=1,
            border_color=theme.get("border"),
            height=DIMENSIONS["input_height"] + 4,
        )
        self.search_frame.pack(fill="x", padx=0, pady=0)
        self.search_frame.pack_propagate(False)
        
        # Icône loupe
        self.icon_label = Icon(
            self.search_frame,
            "search",
            size=17,
            color="text_muted",
            background="bg_input",
        )
        self.icon_label.pack(side="left", padx=(14, 0))
        
        # Champ de saisie
        self.entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un compte...",
            font=FONTS["body"],
            fg_color="transparent",
            border_width=0,
            text_color=theme.get("text_primary"),
            placeholder_text_color=theme.get("text_muted"),
            height=DIMENSIONS["input_height"] - 2,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry.bind("<FocusIn>", self._on_focus_in, add="+")
        self.entry.bind("<FocusOut>", self._on_focus_out, add="+")
        
        # Détecte la frappe pour chercher en temps réel
        self.entry.bind("<KeyRelease>", self._on_key)
    
    def _on_key(self, event=None):
        if self.on_search:
            self.on_search(self.entry.get())

    def _on_focus_in(self, event=None):
        self._search_focused = True
        self.search_frame.configure(border_color=theme.get("border_focus"))

    def _on_focus_out(self, event=None):
        self._search_focused = False
        self.search_frame.configure(border_color=theme.get("border"))
    
    def get_query(self) -> str:
        return self.entry.get()
    
    def clear(self):
        self.entry.delete(0, "end")
        if self.on_search:
            self.on_search("")
    
    def apply_theme(self):
        self.search_frame.configure(
            fg_color=theme.get("bg_input"),
            border_color=(
                theme.get("border_focus")
                if self._search_focused
                else theme.get("border")
            ),
        )
        self.icon_label.refresh()
        self.entry.configure(
            text_color=theme.get("text_primary"),
            placeholder_text_color=theme.get("text_muted"),
        )


class AccountCard(ctk.CTkFrame):
    """
    Carte affichant un compte avec nom, login, catégorie et boutons d'action.
    
    ┌──────────────────────────────────────────────────────┐
    │ 🎮  Netflix                           📋 ✏️  🗑️    │
    │     email@gmail.com    ••••••••                      │
    └──────────────────────────────────────────────────────┘
    """
    
    def __init__(self, parent, account, on_copy_password=None, on_copy_login=None,
                 on_edit=None, on_delete=None, on_toggle_favorite=None,
                 on_copy_totp=None, is_weak=False, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.get("bg_card"),
            corner_radius=DIMENSIONS["corner_radius"],
            border_width=1,
            border_color=theme.get("border"),
            cursor="hand2",
            **kwargs
        )
        
        self.account = account
        self.on_copy_password = on_copy_password
        self.on_copy_login = on_copy_login
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_toggle_favorite = on_toggle_favorite
        self.on_copy_totp = on_copy_totp
        self._is_hovered = False
        self._password_visible = False
        self._hover_animation_id = None
        self.is_weak = is_weak
        
        self._build()
        
        # Effets de survol
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _build(self):
        # Conteneur principal avec padding
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=12)
        
        # ── Colonne gauche : icône catégorie ──
        category_tint = blend_colors(
            self.account.category_color,
            theme.get("bg_card"),
            0.12,
        )
        icon_frame = ctk.CTkFrame(
            content,
            fg_color=category_tint,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            width=40,
            height=40,
        )
        icon_frame.pack(side="left", padx=(0, 14))
        icon_frame.pack_propagate(False)
        
        self.category_icon = Icon(
            icon_frame,
            normalize_icon(self.account.category_icon),
            size=21,
            color=self.account.category_color,
            background=category_tint,
        )
        self.category_icon.place(relx=0.5, rely=0.5, anchor="center")
        
        # ── Colonne centrale : nom + login ──
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_row.pack(anchor="w", fill="x")

        name_label = ctk.CTkLabel(
            name_row,
            text=self.account.name,
            font=FONTS["body_bold"],
            text_color=theme.get("text_primary"),
            anchor="w",
        )
        name_label.pack(side="left")

        if self.is_weak:
            ctk.CTkLabel(
                name_row,
                text="À renforcer",
                font=FONTS["caption"],
                fg_color=theme.get("error_light"),
                text_color=theme.get("warning"),
                corner_radius=8,
            ).pack(side="left", padx=(9, 0), ipadx=6, ipady=2)
        
        login_label = ctk.CTkLabel(
            info_frame,
            text=self.account.login if self.account.login else "Aucun identifiant",
            font=FONTS["body_sm"],
            text_color=theme.get("text_secondary"),
            anchor="w",
        )
        login_label.pack(anchor="w")

        password_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        password_row.pack(anchor="w", fill="x", pady=(1, 0))
        self.password_label = ctk.CTkLabel(
            password_row,
            text="••••••••" if self.account.password else "Aucun mot de passe",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
        )
        self.password_label.pack(side="left")
        if self.account.password:
            self.password_reveal_button = IconButton(
                password_row,
                "eye",
                command=self._toggle_password_visibility,
                size=13,
                color="text_muted",
                background="bg_card",
                width=24,
                height=22,
                corner_radius=DIMENSIONS["corner_radius_sm"],
                fg_color="transparent",
                hover_color=theme.get("bg_hover"),
            )
            self.password_reveal_button.button.accessible_name = (
                "Afficher le mot de passe"
            )
            self.password_reveal_button.pack(side="left", padx=(4, 0))
        
        # ── Colonne droite : boutons d'action ──
        actions_frame = ctk.CTkFrame(content, fg_color="transparent")
        actions_frame.pack(side="right", padx=(10, 0))

        favorite_button = IconButton(
            actions_frame,
            "star",
            command=lambda: (
                self.on_toggle_favorite(self.account) if self.on_toggle_favorite else None
            ),
            size=17,
            color="warning" if self.account.favorite else "text_muted",
            background="bg_card",
            width=32,
            height=32,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
        )
        favorite_button.button.accessible_name = (
            "Retirer des favoris" if self.account.favorite else "Ajouter aux favoris"
        )
        favorite_button.pack(side="left", padx=2)

        if self.account.totp_secret or self.account.totp_secret_error:
            totp_button = IconButton(
                actions_frame,
                "warning" if self.account.totp_secret_error else "totp",
                command=lambda: (
                    self.on_copy_totp(self.account) if self.on_copy_totp else None
                ),
                size=17,
                color="error" if self.account.totp_secret_error else "accent",
                background="bg_card",
                width=32,
                height=32,
                corner_radius=DIMENSIONS["corner_radius_sm"],
                fg_color="transparent",
                hover_color=theme.get("bg_hover"),
            )
            totp_button.button.accessible_name = "Copier le code de vérification"
            totp_button.pack(side="left", padx=2)
        
        # Bouton copier login
        btn_copy_login = IconButton(
            actions_frame,
            "user",
            command=lambda: self.on_copy_login(self.account) if self.on_copy_login else None,
            size=17,
            color="text_secondary",
            background="bg_card",
            width=32,
            height=32,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
        )
        btn_copy_login.button.accessible_name = "Copier l’identifiant"
        btn_copy_login.pack(side="left", padx=2)
        
        # Bouton copier mot de passe
        btn_copy_pwd = IconButton(
            actions_frame,
            "key",
            command=lambda: self.on_copy_password(self.account) if self.on_copy_password else None,
            size=17,
            color="accent",
            background="bg_card",
            width=32,
            height=32,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color=theme.get("accent_light"),
            hover_color=theme.get("accent_glow"),
        )
        btn_copy_pwd.button.accessible_name = "Copier le mot de passe"
        btn_copy_pwd.pack(side="left", padx=2)
        
        # Bouton modifier
        btn_edit = IconButton(
            actions_frame,
            "edit",
            command=lambda: self.on_edit(self.account) if self.on_edit else None,
            size=17,
            color="text_secondary",
            background="bg_card",
            width=32,
            height=32,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
        )
        btn_edit.button.accessible_name = "Modifier le compte"
        btn_edit.pack(side="left", padx=2)
        
        # Bouton supprimer
        btn_delete = IconButton(
            actions_frame,
            "trash",
            command=lambda: self.on_delete(self.account) if self.on_delete else None,
            size=17,
            color="text_muted",
            background="bg_card",
            hover_background="error_light",
            width=34,
            height=34,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("error_light"),
        )
        btn_delete.button.accessible_name = "Supprimer le compte"
        btn_delete.pack(side="left", padx=2)

    def _toggle_password_visibility(self):
        self._password_visible = not self._password_visible
        self.password_label.configure(
            text=self.account.password if self._password_visible else "••••••••"
        )
        self.password_reveal_button.icon.name = (
            "eye_off" if self._password_visible else "eye"
        )
        self.password_reveal_button.icon.refresh()
        self.password_reveal_button.button.accessible_name = (
            "Masquer le mot de passe"
            if self._password_visible
            else "Afficher le mot de passe"
        )
    
    def _on_enter(self, event=None):
        self._is_hovered = True
        self._animate_hover_color(True)
    
    def _on_leave(self, event=None):
        self.after_idle(self._check_pointer_inside)

    def _check_pointer_inside(self):
        if not self.winfo_exists():
            return
        widget = self.winfo_containing(*self.winfo_pointerxy())
        while widget is not None:
            if widget is self:
                return
            widget = getattr(widget, "master", None)
        self._is_hovered = False
        self._animate_hover_color(False)

    def _animate_hover_color(self, entering: bool, step: int = 0):
        if self._hover_animation_id is not None:
            self.after_cancel(self._hover_animation_id)
            self._hover_animation_id = None

        steps = 1 if MOTION["reduced"] else 5
        progress = min((step + 1) / steps, 1)
        if entering:
            background = blend_colors(
                theme.get("bg_hover"), theme.get("bg_card"), progress
            )
            border = blend_colors(
                theme.get("border_light"), theme.get("border"), progress
            )
        else:
            background = blend_colors(
                theme.get("bg_card"), theme.get("bg_hover"), progress
            )
            border = blend_colors(
                theme.get("border"), theme.get("border_light"), progress
            )
        self.configure(
            fg_color=background,
            border_color=border,
            border_width=2 if entering else 1,
        )

        if step < steps - 1:
            self._hover_animation_id = self.after(
                max(1, MOTION["fast_ms"] // steps),
                lambda: self._continue_hover_animation(entering, step + 1),
            )

    def _continue_hover_animation(self, entering: bool, step: int):
        self._hover_animation_id = None
        self._animate_hover_color(entering, step)

    def destroy(self):
        if self._hover_animation_id is not None:
            self.after_cancel(self._hover_animation_id)
            self._hover_animation_id = None
        super().destroy()


class CategoryButton(ctk.CTkFrame):
    """
    Bouton de catégorie dans la sidebar.
    
    Affiche l'icône, le nom et le nombre de comptes.
    """
    
    def __init__(self, parent, category=None, label="Tous les comptes", 
                 icon="list", color=None, count=0, is_active=False,
                 on_click=None, **kwargs):
        super().__init__(parent, fg_color="transparent", cursor="hand2", **kwargs)
        
        self.category = category
        self.on_click = on_click
        self.is_active = is_active
        color = theme.get("accent") if color is None else color
        
        # Conteneur
        self.btn_frame = ctk.CTkFrame(
            self,
            fg_color=theme.get("accent_light") if is_active else "transparent",
            corner_radius=DIMENSIONS["corner_radius"],
            height=42,
        )
        self.btn_frame.pack(fill="x", padx=4, pady=2)
        self.btn_frame.pack_propagate(False)
        
        # Barre de couleur à gauche
        self.color_bar = ctk.CTkFrame(
            self.btn_frame,
            fg_color=color if is_active else "transparent",
            width=3,
            corner_radius=2,
        )
        self.color_bar.pack(side="left", fill="y", padx=(6, 0), pady=8)
        self.color_bar.bind("<Button-1>", self._handle_click)
        
        # Icône
        self.icon_label = Icon(
            self.btn_frame,
            normalize_icon(icon),
            size=17,
            color=color if is_active else "text_muted",
            background="accent_light" if is_active else "bg_secondary",
        )
        self.icon_label.pack(side="left", padx=(8, 6))
        
        # Nom
        self.name_label = ctk.CTkLabel(
            self.btn_frame,
            text=label,
            font=FONTS["body_sm_bold"] if is_active else FONTS["body_sm"],
            text_color=theme.get("text_primary") if is_active else theme.get("text_secondary"),
            anchor="w",
        )
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Badge compteur
        if count > 0:
            self.count_label = ctk.CTkLabel(
                self.btn_frame,
                text=str(count),
                font=FONTS["caption"],
                text_color=theme.get("text_secondary"),
                fg_color=theme.get("bg_tertiary"),
                corner_radius=9,
                width=30,
            )
            self.count_label.pack(side="right", padx=(0, 10))
            self.count_label.bind("<Button-1>", self._handle_click)
        
        # Bind click sur tout le frame
        self.btn_frame.bind("<Button-1>", self._handle_click)
        self.icon_label.bind("<Button-1>", self._handle_click)
        self.name_label.bind("<Button-1>", self._handle_click)
        
        # Hover
        self.btn_frame.bind("<Enter>", self._on_enter)
        self.btn_frame.bind("<Leave>", self._on_leave)
    
    def _handle_click(self, event=None):
        if self.on_click:
            self.on_click(self.category)
    
    def _on_enter(self, event=None):
        if not self.is_active:
            self.btn_frame.configure(fg_color=theme.get("bg_hover"))
    
    def _on_leave(self, event=None):
        if not self.is_active:
            self.btn_frame.configure(fg_color="transparent")


class ToastNotification(ctk.CTkFrame):
    """
    Notification temporaire qui apparaît en bas de l'écran.
    
    Exemple : "✅ Mot de passe copié !" pendant 2 secondes
    """
    
    def __init__(self, parent, message: str, toast_type: str = "success", 
                 duration_ms: int = 2500, **kwargs):
        
        colors = {
            "success": ("success", "check"),
            "error": ("error", "error"),
            "info": ("info", "info"),
            "warning": ("warning", "warning"),
        }
        color, icon = colors.get(toast_type, colors["info"])
        color = theme.get(color)
        
        super().__init__(
            parent,
            fg_color=theme.get("bg_secondary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            border_width=1,
            border_color=blend_colors(color, theme.get("bg_secondary"), 0.35),
            **kwargs
        )
        
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=16, pady=10)
        
        # Icône
        Icon(
            inner,
            icon,
            size=17,
            color=color,
            background="bg_secondary",
        ).pack(side="left", padx=(0, 8))
        
        # Message
        ctk.CTkLabel(
            inner,
            text=message,
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_primary"),
        ).pack(side="left")
        
        self._target_rely = 0.95
        self._animation_after_id = None
        self._dismiss_after_id = self.after(duration_ms, self._fade_out)

    def animate_in(self):
        if MOTION["reduced"]:
            return
        self.place_configure(rely=0.98)
        self._animate_position(0.98, self._target_rely, 0)

    def _animate_position(self, start: float, target: float, step: int):
        if not self.winfo_exists():
            return
        steps = 4
        progress = min((step + 1) / steps, 1)
        eased = 1 - (1 - progress) ** 2
        self.place_configure(rely=start + (target - start) * eased)
        if step < steps - 1:
            self._animation_after_id = self.after(
                max(1, MOTION["fast_ms"] // steps),
                lambda: self._animate_position(start, target, step + 1),
            )
        else:
            self._animation_after_id = None

    def _fade_out(self):
        self._dismiss_after_id = None
        if MOTION["reduced"]:
            self.destroy()
            return
        if self._animation_after_id is not None:
            self.after_cancel(self._animation_after_id)
            self._animation_after_id = None
        current_rely = float(self.place_info().get("rely", self._target_rely))
        self._animate_position(current_rely, 1.02, 0)
        self._destroy_after_id = self.after(
            MOTION["fast_ms"],
            self._destroy_after_slide,
        )

    def _destroy_after_slide(self):
        self._destroy_after_id = None
        self.destroy()

    def destroy(self):
        if self._animation_after_id is not None:
            self.after_cancel(self._animation_after_id)
            self._animation_after_id = None
        if self._dismiss_after_id is not None:
            self.after_cancel(self._dismiss_after_id)
            self._dismiss_after_id = None
        if getattr(self, "_destroy_after_id", None) is not None:
            self.after_cancel(self._destroy_after_id)
            self._destroy_after_id = None
        super().destroy()
