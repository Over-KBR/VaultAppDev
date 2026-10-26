"""
Écran principal de VaultApp.

C'est l'écran qu'on voit après le déverrouillage :
- Sidebar gauche avec les catégories
- Zone centrale avec la barre de recherche et la liste des comptes
"""

import customtkinter as ctk
import time
from tkinter import messagebox
from typing import Optional
from src.ui.theme import theme, FONTS, DIMENSIONS, MOTION, button_style
from src.ui.components import SearchBar, AccountCard, CategoryButton, ToastNotification
from src.ui.icons import Icon, IconButton, refresh_icons
from src.ui.account_dialog import AccountDialog
from src.ui.category_dialog import CategoryDialog
from src.models import Account, Category
from src.clipboard import copy_to_clipboard, get_clipboard_clear_seconds
from src.totp import generate_totp_code, seconds_until_next_code
from src.strength import is_weak
from src import database as db
from src.ui.dashboard_screen import DashboardScreen
from src.debug_console import traced_action


class MainScreen(ctk.CTkFrame):
    """Écran principal avec sidebar catégories + liste des comptes."""
    
    def __init__(self, parent, encryption_key: bytes, on_theme_toggle=None,
                 debug_mode: bool = False, **kwargs):
        super().__init__(parent, fg_color=theme.get("bg_primary"), **kwargs)
        
        self.encryption_key = encryption_key
        self.on_theme_toggle = on_theme_toggle
        self.debug_mode = debug_mode
        self.debug_console = getattr(parent, "debug_console", None) if debug_mode else None
        self.selected_category_id = None  # None = toutes les catégories
        self.search_query = ""
        self.is_dashboard_active = False
        self.is_favorites_active = False
        self._search_after_id = None
        self._view_animation_id = None
        self._categories_cache = []
        self._account_count = 0
        self._favorite_count = 0

        # V2 : verrouillage automatique + scan mots de passe faibles
        self._lock_timer_id = None
        self._weak_account_ids: set = set()

        if self.debug_mode:
            debug_banner = ctk.CTkFrame(
                self,
                fg_color=theme.get("accent_light"),
                corner_radius=0,
                height=30,
            )
            debug_banner.pack(side="top", fill="x")
            debug_banner.pack_propagate(False)
            Icon(
                debug_banner,
                "info",
                size=14,
                color="accent",
                background="accent_light",
            ).pack(side="left", padx=(14, 8))
            ctk.CTkLabel(
                debug_banner,
                text="MODE DEBUG | coffre fictif temporaire | presse-papiers et API désactivés",
                fg_color="transparent",
                text_color=theme.get("accent"),
                font=FONTS["caption"],
            ).pack(side="left")
        self._build()
        self._refresh_all()
        self._reset_lock_timer()

        # Réinitialise le timer à chaque activité
        self._activity_top_level = self.winfo_toplevel()
        self._activity_binding_ids = (
            (
                "<Motion>",
                self._activity_top_level.bind(
                    "<Motion>", self._on_activity, add="+"
                ),
            ),
            (
                "<KeyPress>",
                self._activity_top_level.bind(
                    "<KeyPress>", self._on_activity, add="+"
                ),
            ),
        )
    
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

    def destroy(self):
        """Annule les rappels différés et les événements globaux avant destruction."""
        self._cancel_pending_search()
        self._cancel_view_animation()
        if self._lock_timer_id is not None:
            self.after_cancel(self._lock_timer_id)
            self._lock_timer_id = None
        if self._activity_top_level.winfo_exists():
            for sequence, binding_id in self._activity_binding_ids:
                if binding_id:
                    self._activity_top_level.unbind(sequence, binding_id)
        super().destroy()

    def _cancel_pending_search(self):
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None

    def _cancel_view_animation(self):
        if self._view_animation_id is not None:
            self.after_cancel(self._view_animation_id)
            self._view_animation_id = None

    def _animate_view_in(self, view, bottom_padding=0):
        self._cancel_view_animation()
        if MOTION["reduced"]:
            view.pack_configure(pady=(0, bottom_padding))
            return

        steps = 4
        view.pack_configure(pady=(8, bottom_padding))

        def advance(step):
            if not view.winfo_exists():
                self._view_animation_id = None
                return
            remaining = round(8 * (1 - (step + 1) / steps))
            view.pack_configure(pady=(remaining, bottom_padding))
            if step + 1 < steps:
                self._view_animation_id = self.after(
                    max(1, MOTION["fast_ms"] // steps),
                    lambda: advance(step + 1),
                )
            else:
                self._view_animation_id = None

        advance(0)
    
    def _build_sidebar(self):
        """Construit la sidebar avec les catégories."""
        
        brand_inner = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_inner.pack(fill="x", padx=18, pady=(20, 20))
        logo = ctk.CTkFrame(
            brand_inner,
            fg_color=theme.get("accent"),
            corner_radius=10,
            width=34,
            height=34,
        )
        logo.pack(side="left", padx=(0, 10))
        logo.pack_propagate(False)
        Icon(
            logo,
            "vault",
            size=19,
            color="text_on_accent",
            background="accent",
        ).place(relx=0.5, rely=0.5, anchor="center")

        brand_text = ctk.CTkFrame(brand_inner, fg_color="transparent")
        brand_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            brand_text,
            text="VaultApp",
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
            anchor="w",
        ).pack(anchor="w")

        controls = ctk.CTkFrame(brand_inner, fg_color="transparent")
        controls.pack(side="right", padx=(4, 0))
        
        # Bouton Paramètres
        settings_button = IconButton(
            controls,
            "settings",
            command=self._open_settings,
            color="text_secondary",
            background="bg_secondary",
            width=30,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
        )
        settings_button.button.accessible_name = "Ouvrir les paramètres"
        settings_button.pack(side="left", padx=(0, 5))

        # Toggle thème
        theme_btn = IconButton(
            controls,
            "sun" if theme.is_dark() else "moon",
            command=self._toggle_theme,
            color="accent",
            background="bg_secondary",
            size=19,
            width=30,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
        )
        theme_btn.button.accessible_name = "Changer le thème"
        theme_btn.pack(side="left")
        self._theme_btn = theme_btn.button
        self._theme_icon = theme_btn.icon

        ctk.CTkFrame(
            self.sidebar,
            fg_color=theme.get("border"),
            height=1,
        ).pack(fill="x", padx=18, pady=(0, 14))
        
        # ── Zone de navigation fixe (Tous les comptes / Audit) ──
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=(0, 18))
        
        # ── Titre catégories ──
        cat_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        cat_header.pack(fill="x", padx=18, pady=(4, 8))
        
        ctk.CTkLabel(
            cat_header,
            text="CATÉGORIES",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
        ).pack(side="left")
        
        # Bouton ajouter catégorie
        add_category_button = IconButton(
            cat_header,
            "plus",
            command=self._add_category,
            color="text_secondary",
            background="bg_secondary",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
        )
        add_category_button.button.accessible_name = "Ajouter une catégorie"
        add_category_button.pack(side="right")
        
        # ── Liste des catégories (scrollable) ──
        self.categories_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
        )
        self.categories_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        # ── Footer sidebar ──
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        ctk.CTkFrame(
            self.sidebar,
            fg_color=theme.get("border"),
            height=1,
        ).pack(fill="x", padx=18, pady=(0, 12))
        footer.pack(fill="x", padx=18, pady=(0, 18))
        
        self.stats_label = ctk.CTkLabel(
            footer,
            text="",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
        )
        self.stats_label.pack()
        ctk.CTkLabel(
            footer,
            text="Chiffrement local · AES-256-GCM",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
        ).pack(pady=(5, 0))
    
    def _build_main_content(self):
        """Construit la zone de contenu principal."""
        
        # ── Header ──
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=42, pady=(32, 22))
        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.pack(side="left", fill="x", expand=True)

        self.title_label = ctk.CTkLabel(
            title_block,
            text="Tous les comptes",
            font=FONTS["heading"],
            text_color=theme.get("text_primary"),
            anchor="w",
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(
            title_block,
            text="Tous vos accès, protégés au même endroit.",
            font=FONTS["body"],
            text_color=theme.get("text_muted"),
            anchor="w",
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))
        
        # Bouton ajouter un compte
        self.add_btn = ctk.CTkButton(
            header,
            text="Ajouter un compte",
            font=FONTS["body_bold"],
            width=156,
            **button_style("primary", height=40),
            command=self._add_account,
        )
        self.add_btn.pack(side="right", anchor="center", padx=(16, 0))
        
        # ── Vue des Comptes (Recherche + Liste) ──
        self.accounts_view = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.accounts_view.pack(fill="both", expand=True)
        
        # ── Barre de recherche ──
        self.search_bar = SearchBar(
            self.accounts_view,
            on_search=self._on_search,
        )
        self.search_bar.pack(fill="x", padx=42, pady=(0, 20))
        
        # ── Liste des comptes (scrollable) ──
        self.accounts_frame = ctk.CTkScrollableFrame(
            self.accounts_view,
            fg_color="transparent",
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
        )
        self.accounts_frame.pack(fill="both", expand=True, padx=42, pady=(0, 28))
        
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
        accounts = db.get_all_accounts(self.encryption_key)
        self._account_count = len(accounts)
        self._favorite_count = sum(account.favorite for account in accounts)
        self._categories_cache = db.get_all_categories()
        self._scan_weak_passwords(accounts)
        self._refresh_categories()
        if self.is_dashboard_active:
            self.dashboard_view.refresh_data(accounts)
        else:
            self._refresh_accounts(accounts)
        self._refresh_stats()
    
    def _refresh_categories(self):
        """Rafraîchit la liste des catégories dans la sidebar."""
        # Vider les deux zones
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        
        categories = self._categories_cache
        total = self._account_count
        
        # Bouton fixe "Tous les comptes"
        CategoryButton(
            self.nav_frame,
            label="Tous les comptes",
            icon="list",
            color=theme.get("accent"),
            count=total,
            is_active=(
                not self.is_dashboard_active
                and not self.is_favorites_active
                and self.selected_category_id is None
            ),
            on_click=lambda _: self._select_category(None),
        ).pack(fill="x", pady=1)

        CategoryButton(
            self.nav_frame,
            label="Favoris",
            icon="star",
            color=theme.get("warning"),
            count=self._favorite_count,
            is_active=self.is_favorites_active,
            on_click=lambda _: self._select_favorites(),
        ).pack(fill="x", pady=1)

        # Bouton fixe "Audit de sécurité"
        CategoryButton(
            self.nav_frame,
            label="Audit de sécurité",
            icon="shield_check",
            color=theme.get("error"),
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
    
    def _refresh_accounts(self, accounts=None):
        """Rafraîchit la liste des comptes."""
        # Vider la liste
        for widget in self.accounts_frame.winfo_children():
            if widget is not self.empty_frame:
                widget.destroy()
        
        # Cacher le message vide
        self.empty_frame.pack_forget()
        
        if accounts is None:
            accounts = db.get_all_accounts(
                self.encryption_key,
                category_id=None if self.is_favorites_active else self.selected_category_id,
                search_query=self.search_query,
            )
        else:
            query = self.search_query.casefold()
            accounts = [
                account for account in accounts
                if (self.selected_category_id is None
                    or account.category_id == self.selected_category_id)
                and (not self.is_favorites_active or account.favorite)
                and (not query or query in account.name.casefold()
                     or query in account.login.casefold()
                     or query in account.url.casefold())
            ]
        if self.is_favorites_active and accounts is not None:
            accounts = [account for account in accounts if account.favorite]
        
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
                on_toggle_favorite=self._toggle_favorite,
                on_copy_totp=self._copy_totp_code,
                is_weak=account.id in self._weak_account_ids,
            )
            card.pack(fill="x", pady=4)
    
    def _refresh_stats(self):
        """Met à jour les stats dans le footer."""
        self.stats_label.configure(
            text=f"{self._account_count} comptes · {len(self._categories_cache)} catégories"
        )
    
    def _show_empty_state(self):
        """Affiche un message quand il n'y a pas de comptes."""
        for widget in self.empty_frame.winfo_children():
            widget.destroy()
        self.empty_frame.pack(fill="both", expand=True, pady=60)
        
        Icon(
            self.empty_frame,
            "lock",
            size=38,
            color="accent",
            background="bg_primary",
        ).pack(pady=(0, 16))
        
        if self.search_query:
            text = "Aucun résultat trouvé"
            subtext = "Essaie avec d'autres mots-clés"
        elif self.is_favorites_active:
            text = "Aucun favori pour le moment"
            subtext = "Utilisez l’étoile sur un compte pour l’ajouter aux favoris."
        else:
            text = "Aucun compte pour le moment"
            subtext = "Utilisez le bouton Ajouter pour commencer."
        
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
    
    @traced_action(
        "Afficher les comptes",
        "La liste doit correspondre à la catégorie sélectionnée et à la recherche active.",
    )
    def _select_category(self, category_id: Optional[int]):
        """Sélectionne une catégorie dans la sidebar."""
        self._cancel_pending_search()
        self.is_dashboard_active = False
        self.is_favorites_active = False
        self.selected_category_id = category_id
        
        # Afficher la vue des comptes
        self.dashboard_view.pack_forget()
        self.accounts_view.pack(fill="both", expand=True)
        self._animate_view_in(self.accounts_view)
        self.add_btn.pack(side="right")
        
        # Mettre à jour le titre
        if category_id is None:
            self.title_label.configure(text="Tous les comptes")
            self.subtitle_label.configure(
                text="Retrouvez vos accès, simplement et en sécurité."
            )
        else:
            for cat in self._categories_cache:
                if cat.id == category_id:
                    self.title_label.configure(text=cat.name)
                    self.subtitle_label.configure(
                        text=f"Les identifiants enregistrés dans {cat.name}."
                    )
                    break
        
        self._refresh_categories()
        self._refresh_accounts()

    @traced_action(
        "Ouvrir l'audit",
        "Le score et les alertes doivent être recalculés à partir des comptes fictifs.",
    )
    def _select_dashboard(self):
        """Affiche le tableau de bord de sécurité."""
        self._cancel_pending_search()
        self.is_dashboard_active = True
        self.is_favorites_active = False
        self.selected_category_id = None
        
        # Afficher le dashboard
        self.accounts_view.pack_forget()
        self.add_btn.pack_forget()
        self.dashboard_view.pack(fill="both", expand=True, padx=34, pady=(0, 24))
        self.dashboard_view.refresh_data(db.get_all_accounts(self.encryption_key))
        self._animate_view_in(self.dashboard_view, bottom_padding=24)
        
        self.title_label.configure(text="Audit de sécurité")
        self.subtitle_label.configure(
            text="Un aperçu clair pour renforcer la sécurité de votre coffre."
        )
        self._refresh_categories()

    @traced_action(
        "Afficher les favoris",
        "Seuls les comptes marqués d'une étoile doivent apparaître.",
    )
    def _select_favorites(self):
        """Affiche les comptes favoris."""
        self._cancel_pending_search()
        self.is_dashboard_active = False
        self.is_favorites_active = True
        self.selected_category_id = None
        self.dashboard_view.pack_forget()
        self.accounts_view.pack(fill="both", expand=True)
        self._animate_view_in(self.accounts_view)
        self.add_btn.pack(side="right")
        self.title_label.configure(text="Favoris")
        self.subtitle_label.configure(
            text="Vos accès importants, réunis au même endroit."
        )
        self._refresh_categories()
        self._refresh_accounts()

    @traced_action(
        "Modifier un favori",
        "L'étoile, le compteur de favoris et la vue active doivent être actualisés.",
    )
    def _toggle_favorite(self, account: Account):
        """Bascule l'état favori d'un compte."""
        favorite = not account.favorite
        db.set_account_favorite(account.id, favorite)
        account.favorite = favorite
        self._favorite_count += 1 if account.favorite else -1
        self._refresh_categories()
        self._refresh_accounts()
        state = "ajouté aux" if account.favorite else "retiré des"
        self._show_toast(f"« {account.name} » {state} favoris")
    
    def _on_search(self, query: str):
        """Callback de la barre de recherche."""
        self.search_query = query
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(120, self._run_search)

    def _run_search(self):
        self._search_after_id = None
        self._refresh_accounts()
    
    @traced_action(
        "Copier un mot de passe",
        "En mode debug, l'action doit être bloquée et le presse-papiers doit rester inchangé.",
    )
    def _copy_password(self, account: Account):
        """Copie le mot de passe dans le presse-papier."""
        if self.debug_mode:
            self._show_toast("Copie désactivée en mode debug")
            return
        if account.password:
            seconds = get_clipboard_clear_seconds()
            copy_to_clipboard(account.password, clear_after_seconds=seconds)
            self._show_toast(f"Mot de passe copié (effacé dans {seconds} s)")
    
    @traced_action(
        "Copier un identifiant",
        "En mode debug, l'action doit être bloquée et le presse-papiers doit rester inchangé.",
    )
    def _copy_login(self, account: Account):
        """Copie le login dans le presse-papier."""
        if self.debug_mode:
            self._show_toast("Copie désactivée en mode debug")
            return
        if account.login:
            seconds = get_clipboard_clear_seconds()
            copy_to_clipboard(account.login, clear_after_seconds=seconds)
            self._show_toast(f"Identifiant copié (effacé dans {seconds} s)")

    @traced_action(
        "Copier un code TOTP",
        "En mode normal, calcul local puis copie avec effacement au plus tard à l'expiration ; en debug, copie bloquée.",
    )
    def _copy_totp_code(self, account: Account):
        """Génère et copie le code TOTP courant."""
        if self.debug_mode:
            self._show_toast("Copie désactivée en mode debug")
            return
        if account.totp_secret_error:
            self._show_toast("Secret TOTP illisible : remplace-le dans la fiche du compte", "error")
            return
        current_time = time.time()
        code = generate_totp_code(account.totp_secret, timestamp=current_time)
        remaining = seconds_until_next_code(timestamp=current_time)
        clear_after = min(get_clipboard_clear_seconds(), remaining)
        copy_to_clipboard(code, clear_after_seconds=clear_after)
        self._show_toast(
            f"Code {code} copié · expire dans {remaining} s",
            duration_ms=min(2500, remaining * 1000),
        )
    
    @traced_action(
        "Ouvrir le formulaire de compte",
        "Le formulaire apparaît ; aucune donnée n'est ajoutée avant la sauvegarde.",
    )
    def _add_account(self):
        """Ouvre le dialogue d'ajout de compte."""
        categories = db.get_all_categories()
        AccountDialog(
            self,
            categories=categories,
            on_save=self._save_new_account,
            encryption_key=self.encryption_key,
        )
    
    @traced_action(
        "Enregistrer un compte fictif",
        "Le mot de passe et les notes sont chiffrés dans le coffre temporaire puis la liste est actualisée.",
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
            totp_secret=data["totp_secret"],
        )
        self._refresh_all()
        self._show_toast(f"« {data['name']} » ajouté.")
    
    @traced_action(
        "Ouvrir la modification d'un compte",
        "Le formulaire doit afficher les données fictives du compte sélectionné.",
    )
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
    
    @traced_action(
        "Modifier un compte fictif",
        "Le compte est actualisé et l'ancien mot de passe est conservé dans l'historique si nécessaire.",
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
            totp_secret=data["totp_secret"],
        )
        self._refresh_all()
        self._show_toast(f"« {data['name']} » modifié.")
    
    @traced_action(
        "Supprimer un compte fictif",
        "Une confirmation précède la suppression ; seul le coffre temporaire est concerné.",
    )
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
            self._show_toast(f"« {account.name} » supprimé.")
    
    def _add_category(self):
        """Ouvre le dialogue d'ajout de catégorie."""
        CategoryDialog(
            self,
            on_save=self._save_new_category,
        )
    
    @traced_action(
        "Créer une catégorie fictive",
        "La catégorie doit apparaître dans la navigation après enregistrement.",
    )
    def _save_new_category(self, data: dict):
        """Sauvegarde une nouvelle catégorie."""
        db.add_category(data["name"], data["color"], data["icon"])
        self._refresh_all()
        self._show_toast(f"Catégorie « {data['name']} » créée.")
    
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
            text="Modifier",
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
            text="Supprimer",
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
    
    @traced_action(
        "Modifier une catégorie fictive",
        "Le nom, la couleur et l'icône sont enregistrés puis affichés dans la navigation.",
    )
    def _save_edited_category(self, cat_id: int, data: dict):
        """Sauvegarde les modifications d'une catégorie."""
        db.update_category(cat_id, data["name"], data["color"], data["icon"])
        self._refresh_all()
        self._show_toast(f"Catégorie « {data['name']} » modifiée.")
    
    @traced_action(
        "Supprimer une catégorie fictive",
        "Une confirmation est demandée ; ses comptes restent présents sans catégorie.",
    )
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
            self._show_toast(f"Catégorie « {category.name} » supprimée.")
    
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
        self._lock_timer_id = None
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

    def _scan_weak_passwords(self, accounts=None):
        """Scanne la base pour détecter les mots de passe faibles ou identiques."""
        if accounts is None:
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

    @traced_action(
        "Ouvrir les paramètres",
        "La fenêtre des paramètres doit s'ouvrir au-dessus de l'écran principal.",
    )
    def _open_settings(self):
        """Ouvre la fenêtre de paramètres."""
        from src.ui.settings_screen import SettingsScreen
        SettingsScreen(
            self,
            encryption_key=self.encryption_key,
            on_master_password_changed=self._on_master_password_changed,
            on_theme_changed=self.apply_theme,
            on_vault_imported=self._refresh_all,
            debug_console=self.debug_console,
        )

    def _on_master_password_changed(self, new_key: bytes):
        """Appelé après changement du mot de passe maître — verrouille l'app."""
        master = self.winfo_toplevel()
        if self.debug_mode and hasattr(master, "_debug_unlock"):
            master._debug_unlock(new_key)
            return
        if hasattr(master, "_show_login"):
            master._show_login()

    @traced_action(
        "Changer le thème",
        "L'interface doit passer au thème clair ou sombre sans modifier les données.",
    )
    def _toggle_theme(self):
        """Bascule le thème sombre/clair."""
        if self.on_theme_toggle:
            self.on_theme_toggle()
    
    def _show_toast(
        self, message: str, toast_type: str = "success", duration_ms: int = 2500
    ):
        """Affiche une notification temporaire."""
        toast = ToastNotification(
            self,
            message=message,
            toast_type=toast_type,
            duration_ms=duration_ms,
        )
        toast.place(relx=0.5, rely=0.95, anchor="s")
        toast.animate_in()
    
    def apply_theme(self):
        """Applique le thème actuel à tout l'écran."""
        self.configure(fg_color=theme.get("bg_primary"))
        self.sidebar.configure(fg_color=theme.get("bg_secondary"))
        self.main_content.configure(fg_color=theme.get("bg_primary"))
        self.title_label.configure(text_color=theme.get("text_primary"))
        self.subtitle_label.configure(text_color=theme.get("text_muted"))
        if hasattr(self, "_theme_icon"):
            self._theme_icon.name = "sun" if theme.is_dark() else "moon"
            self._theme_icon.refresh()
        if hasattr(self, "winfo_toplevel"):
            refresh_icons(self.winfo_toplevel())
        elif hasattr(self, "winfo_children"):
            refresh_icons(self)
        self.search_bar.apply_theme()
        self.dashboard_view.configure(
            fg_color=theme.get("bg_primary"),
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover")
        )
