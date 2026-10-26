"""
Écran principal de VaultApp.

C'est l'écran qu'on voit après le déverrouillage :
- Sidebar gauche avec les catégories
- Zone centrale avec la barre de recherche et la liste des comptes
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
from src.ui.theme import theme, FONTS, DIMENSIONS
from src.ui.components import SearchBar, AccountCard, CategoryButton, ToastNotification
from src.ui.account_dialog import AccountDialog
from src.ui.category_dialog import CategoryDialog
from src.models import Account, Category
from src.clipboard import copy_to_clipboard
from src.strength import is_weak
from src import database as db
from src.ui.dashboard_screen import DashboardScreen


class MainScreen(ctk.CTkFrame):
    """Écran principal avec sidebar catégories + liste des comptes."""
    
    def __init__(self, parent, encryption_key: bytes, on_theme_toggle=None, **kwargs):
        super().__init__(parent, fg_color=theme.get("bg_primary"), **kwargs)
        
        self.encryption_key = encryption_key
        self.on_theme_toggle = on_theme_toggle
        self.selected_category_id = None  # None = toutes les catégories
        self.search_query = ""
        self.is_dashboard_active = False

        # V2 : verrouillage automatique + scan mots de passe faibles
        self._lock_timer_id = None
        self._weak_account_ids: set = set()

        self._build()
        self._refresh_all()
        self._reset_lock_timer()
        self._scan_weak_passwords()

        # Réinitialise le timer à chaque activité
        self.winfo_toplevel().bind("<Motion>", self._on_activity, add="+")
        self.winfo_toplevel().bind("<KeyPress>", self._on_activity, add="+")
    
    def _build(self):
        # ══════════════════════════════════════════
        # Layout : sidebar | main content
        # ══════════════════════════════════════════
        
        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=theme.get("bg_secondary"),
            corner_radius=0,
            width=DIMENSIONS["sidebar_width"],
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self._build_sidebar()
        
        # ── Séparateur vertical ──
        ctk.CTkFrame(
            self,
            fg_color=theme.get("border"),
            width=1,
        ).pack(side="left", fill="y")
        
        # ── Contenu principal ──
        self.main_content = ctk.CTkFrame(self, fg_color=theme.get("bg_primary"), corner_radius=0)
        self.main_content.pack(side="left", fill="both", expand=True)
        
        self._build_main_content()
    
    def _build_sidebar(self):
        """Construit la sidebar avec les catégories."""
        
        # ── Header sidebar ──
        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(20, 12))
        
        ctk.CTkLabel(
            header,
            text="🔐 VaultApp",
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
            anchor="w",
        ).pack(side="left")
        
        # Bouton Paramètres
        ctk.CTkButton(
            header,
            text="⚙️",
            font=FONTS["icon_sm"],
            width=34, height=34,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_secondary"),
            command=self._open_settings,
        ).pack(side="right", padx=(0, 4))

        # Toggle thème
        theme_btn = ctk.CTkButton(
            header,
            text="🌙" if theme.is_dark() else "☀️",
            font=FONTS["icon_sm"],
            width=34,
            height=34,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_secondary"),
            command=self._toggle_theme,
        )
        theme_btn.pack(side="right")
        self._theme_btn = theme_btn
        
        # ── Séparateur ──
        ctk.CTkFrame(
            self.sidebar,
            fg_color=theme.get("border"),
            height=1,
        ).pack(fill="x", padx=16, pady=(0, 8))
        
        # ── Zone de navigation fixe (Tous les comptes / Audit) ──
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        # ── Titre catégories ──
        cat_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        cat_header.pack(fill="x", padx=16, pady=(8, 4))
        
        ctk.CTkLabel(
            cat_header,
            text="CATÉGORIES",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
        ).pack(side="left")
        
        # Bouton ajouter catégorie
        ctk.CTkButton(
            cat_header,
            text="＋",
            font=("Segoe UI", 16, "bold"),
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_muted"),
            command=self._add_category,
        ).pack(side="right")
        
        # ── Liste des catégories (scrollable) ──
        self.categories_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
        )
        self.categories_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        # ── Footer sidebar ──
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 16))
        
        self.stats_label = ctk.CTkLabel(
            footer,
            text="",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
        )
        self.stats_label.pack()
    
    def _build_main_content(self):
        """Construit la zone de contenu principal."""
        
        # ── Header ──
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))
        
        # Titre dynamique
        self.title_label = ctk.CTkLabel(
            header,
            text="Tous les comptes",
            font=FONTS["heading"],
            text_color=theme.get("text_primary"),
            anchor="w",
        )
        self.title_label.pack(side="left")
        
        # Bouton ajouter un compte
        self.add_btn = ctk.CTkButton(
            header,
            text="＋  Ajouter",
            font=FONTS["body_bold"],
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text_on_accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=38,
            width=130,
            command=self._add_account,
        )
        self.add_btn.pack(side="right")
        
        # ── Vue des Comptes (Recherche + Liste) ──
        self.accounts_view = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.accounts_view.pack(fill="both", expand=True)
        
        # ── Barre de recherche ──
        self.search_bar = SearchBar(
            self.accounts_view,
            on_search=self._on_search,
        )
        self.search_bar.pack(fill="x", padx=24, pady=(0, 16))
        
        # ── Liste des comptes (scrollable) ──
        self.accounts_frame = ctk.CTkScrollableFrame(
            self.accounts_view,
            fg_color="transparent",
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
        )
        self.accounts_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        
        # ── Vue Dashboard (Tableau de bord de sécurité) ──
        self.dashboard_view = DashboardScreen(
            self.main_content,
            encryption_key=self.encryption_key,
            on_edit_account=self._edit_account,
        )
        
        # ── État vide ──
        self.empty_frame = ctk.CTkFrame(self.accounts_frame, fg_color="transparent")
    
    # ══════════════════════════════════════════════════════════════
    # Rafraîchissement des données
    # ══════════════════════════════════════════════════════════════
    
    def _refresh_all(self):
        """Rafraîchit la sidebar et le contenu principal actif."""
        self._refresh_categories()
        if self.is_dashboard_active:
            self.dashboard_view.refresh_data()
        else:
            self._refresh_accounts()
        self._refresh_stats()
    
    def _refresh_categories(self):
        """Rafraîchit la liste des catégories dans la sidebar."""
        # Vider les deux zones
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        
        categories = db.get_all_categories()
        total = db.get_total_account_count()
        
        # Bouton fixe "Tous les comptes"
        CategoryButton(
            self.nav_frame,
            label="Tous les comptes",
            icon="📋",
            color="#7c5cfc",
            count=total,
            is_active=(not self.is_dashboard_active and self.selected_category_id is None),
            on_click=lambda _: self._select_category(None),
        ).pack(fill="x", pady=1)

        # Bouton fixe "Audit de sécurité"
        CategoryButton(
            self.nav_frame,
            label="Audit de sécurité",
            icon="🛡️",
            color="#ef4444",
            count=0,
            is_active=self.is_dashboard_active,
            on_click=lambda _: self._select_dashboard(),
        ).pack(fill="x", pady=1)
        
        # Catégories défilantes
        for cat in categories:
            cat_btn = CategoryButton(
                self.categories_frame,
                category=cat,
                label=cat.name,
                icon=cat.icon,
                color=cat.color,
                count=cat.account_count,
                is_active=(not self.is_dashboard_active and self.selected_category_id == cat.id),
                on_click=lambda c: self._select_category(c.id if c else None),
            )
            cat_btn.pack(fill="x", pady=1)
            
            # Clic droit pour modifier/supprimer
            cat_btn.bind("<Button-3>", lambda e, c=cat: self._show_category_context(e, c))
    
    def _refresh_accounts(self):
        """Rafraîchit la liste des comptes."""
        # Vider la liste
        for widget in self.accounts_frame.winfo_children():
            widget.destroy()
        
        # Cacher le message vide
        self.empty_frame.pack_forget()
        
        accounts = db.get_all_accounts(
            self.encryption_key,
            category_id=self.selected_category_id,
            search_query=self.search_query,
        )
        
        if not accounts:
            self._show_empty_state()
            return
        
        for account in accounts:
            card = AccountCard(
                self.accounts_frame,
                account=account,
                on_copy_password=self._copy_password,
                on_copy_login=self._copy_login,
                on_edit=self._edit_account,
                on_delete=self._delete_account,
                is_weak=account.id in self._weak_account_ids,
            )
            card.pack(fill="x", pady=4)
    
    def _refresh_stats(self):
        """Met à jour les stats dans le footer."""
        total = db.get_total_account_count()
        cats = len(db.get_all_categories())
        self.stats_label.configure(text=f"{total} comptes · {cats} catégories")
    
    def _show_empty_state(self):
        """Affiche un message quand il n'y a pas de comptes."""
        self.empty_frame = ctk.CTkFrame(self.accounts_frame, fg_color="transparent")
        self.empty_frame.pack(fill="both", expand=True, pady=60)
        
        ctk.CTkLabel(
            self.empty_frame,
            text="🔐",
            font=("Segoe UI Emoji", 48),
        ).pack(pady=(0, 16))
        
        if self.search_query:
            text = "Aucun résultat trouvé"
            subtext = "Essaie avec d'autres mots-clés"
        else:
            text = "Aucun compte pour le moment"
            subtext = "Clique sur « ＋ Ajouter » pour commencer"
        
        ctk.CTkLabel(
            self.empty_frame,
            text=text,
            font=FONTS["heading_sm"],
            text_color=theme.get("text_secondary"),
        ).pack(pady=(0, 6))
        
        ctk.CTkLabel(
            self.empty_frame,
            text=subtext,
            font=FONTS["body_sm"],
            text_color=theme.get("text_muted"),
        ).pack()
    
    # ══════════════════════════════════════════════════════════════
    # Actions
    # ══════════════════════════════════════════════════════════════
    
    def _select_category(self, category_id: Optional[int]):
        """Sélectionne une catégorie dans la sidebar."""
        self.is_dashboard_active = False
        self.selected_category_id = category_id
        
        # Afficher la vue des comptes
        self.dashboard_view.pack_forget()
        self.accounts_view.pack(fill="both", expand=True)
        self.add_btn.pack(side="right")
        
        # Mettre à jour le titre
        if category_id is None:
            self.title_label.configure(text="Tous les comptes")
        else:
            cats = db.get_all_categories()
            for cat in cats:
                if cat.id == category_id:
                    self.title_label.configure(text=f"{cat.icon}  {cat.name}")
                    break
        
        self._refresh_categories()
        self._refresh_accounts()

    def _select_dashboard(self):
        """Affiche le tableau de bord de sécurité."""
        self.is_dashboard_active = True
        self.selected_category_id = None
        
        # Afficher le dashboard
        self.accounts_view.pack_forget()
        self.add_btn.pack_forget()
        self.dashboard_view.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self.dashboard_view.refresh_data()
        
        self.title_label.configure(text="🛡️  Audit de sécurité")
        self._refresh_categories()
    
    def _on_search(self, query: str):
        """Callback de la barre de recherche."""
        self.search_query = query
        self._refresh_accounts()
    
    def _copy_password(self, account: Account):
        """Copie le mot de passe dans le presse-papier."""
        if account.password:
            copy_to_clipboard(account.password)
            self._show_toast("🔑 Mot de passe copié ! (effacé dans 30s)")
    
    def _copy_login(self, account: Account):
        """Copie le login dans le presse-papier."""
        if account.login:
            copy_to_clipboard(account.login, clear_after_seconds=0)
            self._show_toast("👤 Login copié !")
    
    def _add_account(self):
        """Ouvre le dialogue d'ajout de compte."""
        categories = db.get_all_categories()
        AccountDialog(
            self,
            categories=categories,
            on_save=self._save_new_account,
            encryption_key=self.encryption_key,
        )
    
    def _save_new_account(self, data: dict):
        """Sauvegarde un nouveau compte."""
        db.add_account(
            name=data["name"],
            login=data["login"],
            password=data["password"],
            url=data["url"],
            notes=data["notes"],
            category_id=data["category_id"],
            encryption_key=self.encryption_key,
        )
        self._refresh_all()
        self._scan_weak_passwords()
        self._show_toast(f"✅ « {data['name']} » ajouté !")
    
    def _edit_account(self, account: Account):
        """Ouvre le dialogue d'édition de compte."""
        categories = db.get_all_categories()
        AccountDialog(
            self,
            categories=categories,
            account=account,
            on_save=lambda data: self._save_edited_account(account.id, data),
            encryption_key=self.encryption_key,
        )
    
    def _save_edited_account(self, account_id: int, data: dict):
        """Sauvegarde les modifications d'un compte."""
        # V2 : sauvegarder l'ancien mot de passe dans l'historique
        from src.history import push_password_history
        accounts = db.get_all_accounts(self.encryption_key)
        old_account = next((a for a in accounts if a.id == account_id), None)
        if old_account and old_account.password != data["password"]:
            push_password_history(account_id, old_account.password, self.encryption_key)

        db.update_account(
            account_id=account_id,
            name=data["name"],
            login=data["login"],
            password=data["password"],
            url=data["url"],
            notes=data["notes"],
            category_id=data["category_id"],
            encryption_key=self.encryption_key,
        )
        self._refresh_all()
        self._scan_weak_passwords()
        self._show_toast(f"✅ « {data['name']} » modifié !")
    
    def _delete_account(self, account: Account):
        """Demande confirmation puis supprime un compte."""
        confirm = messagebox.askyesno(
            "Supprimer le compte",
            f"Es-tu sûr de vouloir supprimer « {account.name} » ?\n\nCette action est irréversible.",
            icon="warning",
        )
        if confirm:
            db.delete_account(account.id)
            self._refresh_all()
            self._show_toast(f"🗑️ « {account.name} » supprimé")
    
    def _add_category(self):
        """Ouvre le dialogue d'ajout de catégorie."""
        CategoryDialog(
            self,
            on_save=self._save_new_category,
        )
    
    def _save_new_category(self, data: dict):
        """Sauvegarde une nouvelle catégorie."""
        db.add_category(data["name"], data["color"], data["icon"])
        self._refresh_all()
        self._show_toast(f"📁 Catégorie « {data['name']} » créée !")
    
    def _show_category_context(self, event, category: Category):
        """Affiche un menu contextuel pour une catégorie (clic droit)."""
        menu = ctk.CTkFrame(
            self,
            fg_color=theme.get("bg_secondary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            border_width=1,
            border_color=theme.get("border"),
        )
        
        # Position du menu
        menu.place(x=event.x_root - self.winfo_rootx(), 
                   y=event.y_root - self.winfo_rooty())
        
        # Modifier
        ctk.CTkButton(
            menu,
            text="✏️  Modifier",
            font=FONTS["body_sm"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_primary"),
            anchor="w",
            height=32,
            command=lambda: [menu.destroy(), self._edit_category(category)],
        ).pack(fill="x", padx=4, pady=(4, 0))
        
        # Supprimer
        ctk.CTkButton(
            menu,
            text="🗑️  Supprimer",
            font=FONTS["body_sm"],
            fg_color="transparent",
            hover_color=theme.get("error_light"),
            text_color=theme.get("error"),
            anchor="w",
            height=32,
            command=lambda: [menu.destroy(), self._delete_category(category)],
        ).pack(fill="x", padx=4, pady=(0, 4))
        
        # Fermer le menu quand on clique ailleurs
        def close_menu(e):
            try:
                menu.destroy()
            except Exception:
                pass
            self.unbind("<Button-1>")
        
        self.bind("<Button-1>", close_menu)
    
    def _edit_category(self, category: Category):
        """Ouvre le dialogue d'édition de catégorie."""
        CategoryDialog(
            self,
            category=category,
            on_save=lambda data: self._save_edited_category(category.id, data),
        )
    
    def _save_edited_category(self, cat_id: int, data: dict):
        """Sauvegarde les modifications d'une catégorie."""
        db.update_category(cat_id, data["name"], data["color"], data["icon"])
        self._refresh_all()
        self._show_toast(f"📁 Catégorie « {data['name']} » modifiée !")
    
    def _delete_category(self, category: Category):
        """Supprime une catégorie."""
        confirm = messagebox.askyesno(
            "Supprimer la catégorie",
            f"Supprimer la catégorie « {category.name} » ?\n\nLes comptes associés ne seront pas supprimés,\nils deviendront « Sans catégorie ».",
            icon="warning",
        )
        if confirm:
            db.delete_category(category.id)
            if self.selected_category_id == category.id:
                self.selected_category_id = None
                self.title_label.configure(text="Tous les comptes")
            self._refresh_all()
            self._show_toast(f"🗑️ Catégorie « {category.name} » supprimée")
    
    # ══════════════════════════════════════════════════════════════
    # V2 — Verrouillage automatique
    # ══════════════════════════════════════════════════════════════

    def _reset_lock_timer(self):
        """Réinitialise le timer de verrouillage automatique."""
        if self._lock_timer_id:
            self.after_cancel(self._lock_timer_id)
            self._lock_timer_id = None

        minutes = int(db.get_setting("auto_lock_minutes", "5"))
        if minutes > 0:
            self._lock_timer_id = self.after(
                minutes * 60 * 1000,
                self._auto_lock,
            )

    def _on_activity(self, event=None):
        """Réinitialise le timer sur toute activité utilisateur."""
        self._reset_lock_timer()

    def _auto_lock(self):
        """Verrouille l'app après inactivité."""
        if hasattr(self, "_locked") and self._locked:
            return
        self._locked = True
        # Appeler le callback de verrouillage dans app.py
        master = self.winfo_toplevel()
        if hasattr(master, "_show_login"):
            master._show_login()

    # ══════════════════════════════════════════════════════════════
    # V2 — Scan mots de passe faibles / doublons
    # ══════════════════════════════════════════════════════════════

    def _scan_weak_passwords(self):
        """Scanne la base pour détecter les mots de passe faibles ou identiques."""
        accounts = db.get_all_accounts(self.encryption_key)
        seen_passwords: dict = {}   # password → account_id
        weak_ids: set = set()

        for acc in accounts:
            pwd = acc.password
            if not pwd:
                continue
            if is_weak(pwd):
                weak_ids.add(acc.id)
            if pwd in seen_passwords:
                weak_ids.add(acc.id)
                weak_ids.add(seen_passwords[pwd])
            else:
                seen_passwords[pwd] = acc.id

        self._weak_account_ids = weak_ids

    # ══════════════════════════════════════════════════════════════
    # V2 — Paramètres
    # ══════════════════════════════════════════════════════════════

    def _open_settings(self):
        """Ouvre la fenêtre de paramètres."""
        from src.ui.settings_screen import SettingsScreen
        SettingsScreen(
            self,
            encryption_key=self.encryption_key,
            on_master_password_changed=self._on_master_password_changed,
            on_theme_changed=self.apply_theme,
        )

    def _on_master_password_changed(self, new_key: bytes):
        """Appelé après changement du mot de passe maître — verrouille l'app."""
        master = self.winfo_toplevel()
        if hasattr(master, "_show_login"):
            master._show_login()

    def _toggle_theme(self):
        """Bascule le thème sombre/clair."""
        if self.on_theme_toggle:
            self.on_theme_toggle()
    
    def _show_toast(self, message: str, toast_type: str = "success"):
        """Affiche une notification temporaire."""
        toast = ToastNotification(
            self,
            message=message,
            toast_type=toast_type,
        )
        toast.place(relx=0.5, rely=0.95, anchor="s")
    
    def apply_theme(self):
        """Applique le thème actuel à tout l'écran."""
        self.configure(fg_color=theme.get("bg_primary"))
        self.sidebar.configure(fg_color=theme.get("bg_secondary"))
        self.main_content.configure(fg_color=theme.get("bg_primary"))
        self.title_label.configure(text_color=theme.get("text_primary"))
        self._theme_btn.configure(text="🌙" if theme.is_dark() else "☀️")
        self.search_bar.apply_theme()
        self.dashboard_view.configure(
            fg_color=theme.get("bg_primary"),
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover")
        )
        self._refresh_all()
