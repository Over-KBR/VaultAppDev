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
from src.ui.theme import theme, FONTS, DIMENSIONS, blend_colors


class SearchBar(ctk.CTkFrame):
    """Barre de recherche avec icône loupe et bouton effacer."""
    
    def __init__(self, parent, on_search=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.on_search = on_search
        
        # Conteneur de la barre
        self.search_frame = ctk.CTkFrame(
            self,
            fg_color=theme.get("bg_input"),
            corner_radius=DIMENSIONS["corner_radius"],
            border_width=1,
            border_color=theme.get("border"),
            height=DIMENSIONS["input_height"],
        )
        self.search_frame.pack(fill="x", padx=0, pady=0)
        self.search_frame.pack_propagate(False)
        
        # Icône loupe
        self.icon_label = ctk.CTkLabel(
            self.search_frame,
            text="🔍",
            font=FONTS["icon_sm"],
            text_color=theme.get("text_muted"),
            width=30,
        )
        self.icon_label.pack(side="left", padx=(12, 0))
        
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
        
        # Détecte la frappe pour chercher en temps réel
        self.entry.bind("<KeyRelease>", self._on_key)
    
    def _on_key(self, event=None):
        if self.on_search:
            self.on_search(self.entry.get())
    
    def get_query(self) -> str:
        return self.entry.get()
    
    def clear(self):
        self.entry.delete(0, "end")
        if self.on_search:
            self.on_search("")
    
    def apply_theme(self):
        self.search_frame.configure(
            fg_color=theme.get("bg_input"),
            border_color=theme.get("border"),
        )
        self.icon_label.configure(text_color=theme.get("text_muted"))
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
                 on_edit=None, on_delete=None, is_weak=False, **kwargs):
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
        self._is_hovered = False
        self._password_visible = False
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
        icon_frame = ctk.CTkFrame(
            content,
            fg_color=blend_colors(self.account.category_color, theme.get("bg_card"), 0.12),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            width=42,
            height=42,
        )
        icon_frame.pack(side="left", padx=(0, 14))
        icon_frame.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(
            icon_frame,
            text=self.account.category_icon,
            font=FONTS["icon"],
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
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
                text="  ⚠️",
                font=FONTS["body_sm"],
                text_color=theme.get("warning"),
                anchor="w",
            ).pack(side="left")
        
        login_label = ctk.CTkLabel(
            info_frame,
            text=self.account.login if self.account.login else "Pas de login",
            font=FONTS["body_sm"],
            text_color=theme.get("text_secondary"),
            anchor="w",
        )
        login_label.pack(anchor="w")
        
        # ── Colonne droite : boutons d'action ──
        actions_frame = ctk.CTkFrame(content, fg_color="transparent")
        actions_frame.pack(side="right", padx=(10, 0))
        
        # Bouton copier login
        btn_copy_login = ctk.CTkButton(
            actions_frame,
            text="👤",
            font=FONTS["icon_sm"],
            width=34,
            height=34,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_secondary"),
            command=lambda: self.on_copy_login(self.account) if self.on_copy_login else None,
        )
        btn_copy_login.pack(side="left", padx=2)
        
        # Bouton copier mot de passe
        btn_copy_pwd = ctk.CTkButton(
            actions_frame,
            text="🔑",
            font=FONTS["icon_sm"],
            width=34,
            height=34,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color=theme.get("accent_light"),
            hover_color=theme.get("accent_glow"),
            text_color=theme.get("accent"),
            command=lambda: self.on_copy_password(self.account) if self.on_copy_password else None,
        )
        btn_copy_pwd.pack(side="left", padx=2)
        
        # Bouton modifier
        btn_edit = ctk.CTkButton(
            actions_frame,
            text="✏️",
            font=FONTS["icon_sm"],
            width=34,
            height=34,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_secondary"),
            command=lambda: self.on_edit(self.account) if self.on_edit else None,
        )
        btn_edit.pack(side="left", padx=2)
        
        # Bouton supprimer
        btn_delete = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            font=FONTS["icon_sm"],
            width=34,
            height=34,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("error_light"),
            text_color=theme.get("text_muted"),
            command=lambda: self.on_delete(self.account) if self.on_delete else None,
        )
        btn_delete.pack(side="left", padx=2)
    
    def _on_enter(self, event=None):
        self._is_hovered = True
        self.configure(
            fg_color=theme.get("bg_hover"),
            border_color=theme.get("border_light"),
        )
    
    def _on_leave(self, event=None):
        self._is_hovered = False
        self.configure(
            fg_color=theme.get("bg_card"),
            border_color=theme.get("border"),
        )


class CategoryButton(ctk.CTkFrame):
    """
    Bouton de catégorie dans la sidebar.
    
    Affiche l'icône, le nom et le nombre de comptes.
    """
    
    def __init__(self, parent, category=None, label="Tous les comptes", 
                 icon="📋", color="#7c5cfc", count=0, is_active=False,
                 on_click=None, **kwargs):
        super().__init__(parent, fg_color="transparent", cursor="hand2", **kwargs)
        
        self.category = category
        self.on_click = on_click
        self.is_active = is_active
        
        # Conteneur
        self.btn_frame = ctk.CTkFrame(
            self,
            fg_color=theme.get("accent_light") if is_active else "transparent",
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=42,
        )
        self.btn_frame.pack(fill="x", padx=4, pady=1)
        self.btn_frame.pack_propagate(False)
        
        # Barre de couleur à gauche
        self.color_bar = ctk.CTkFrame(
            self.btn_frame,
            fg_color=color if is_active else "transparent",
            width=3,
            corner_radius=2,
        )
        self.color_bar.pack(side="left", fill="y", padx=(6, 0), pady=8)
        
        # Icône
        self.icon_label = ctk.CTkLabel(
            self.btn_frame,
            text=icon,
            font=FONTS["icon_sm"],
            width=24,
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
                text_color=theme.get("text_muted"),
                width=28,
            )
            self.count_label.pack(side="right", padx=(0, 10))
        
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
            "success": (theme.get("success"), "✅"),
            "error": (theme.get("error"), "❌"),
            "info": (theme.get("info"), "ℹ️"),
            "warning": (theme.get("warning"), "⚠️"),
        }
        color, icon = colors.get(toast_type, colors["info"])
        
        super().__init__(
            parent,
            fg_color=theme.get("bg_secondary"),
            corner_radius=DIMENSIONS["corner_radius"],
            border_width=1,
            border_color=blend_colors(color, theme.get("bg_secondary"), 0.35),
            **kwargs
        )
        
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=16, pady=10)
        
        # Icône
        ctk.CTkLabel(
            inner,
            text=icon,
            font=FONTS["icon_sm"],
        ).pack(side="left", padx=(0, 8))
        
        # Message
        ctk.CTkLabel(
            inner,
            text=message,
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_primary"),
        ).pack(side="left")
        
        # Auto-destruction après le délai
        self.after(duration_ms, self._fade_out)
    
    def _fade_out(self):
        try:
            self.destroy()
        except Exception:
            pass
