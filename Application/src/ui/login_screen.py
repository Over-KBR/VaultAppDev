"""
Écran de déverrouillage de VaultApp.

Deux modes :
1. Premier lancement → Création du mot de passe maître
2. Lancements suivants → Saisie du mot de passe maître pour déverrouiller
"""

import base64
import customtkinter as ctk
from src.ui.after_callbacks import AfterCallbackMixin
from src.ui.theme import (
    theme,
    FONTS,
    DIMENSIONS,
    bind_entry_focus,
    button_style,
    entry_style,
)
from src.ui.icons import Icon
from src.crypto import generate_salt, derive_key, create_verification_hash, verify_master_password
from src.database import is_first_launch, save_master_config, get_master_config, init_database, create_default_categories


class LoginScreen(AfterCallbackMixin, ctk.CTkFrame):
    """Écran de déverrouillage / création du mot de passe maître."""
    
    def __init__(self, parent, on_unlock=None, **kwargs):
        super().__init__(parent, fg_color=theme.get("bg_primary"), **kwargs)
        self._init_after_callbacks()
        
        self.on_unlock = on_unlock  # Callback appelé quand le mot de passe est validé
        self.is_first = is_first_launch()
        
        self._build()

    def destroy(self):
        self._cancel_after_callbacks()
        super().destroy()
    
    def _build(self):
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=52, pady=38)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(0, weight=1)

        brand_panel = ctk.CTkFrame(shell, fg_color="transparent")
        brand_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 42))

        logo_frame = ctk.CTkFrame(
            brand_panel,
            fg_color=theme.get("accent_light"),
            corner_radius=18,
            width=64,
            height=64,
        )
        logo_frame.pack(anchor="w", pady=(0, 22))
        logo_frame.pack_propagate(False)
        Icon(
            logo_frame,
            "vault",
            size=34,
            color="accent",
            background="accent_light",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            brand_panel,
            text="VaultApp",
            font=FONTS["heading_xl"],
            text_color=theme.get("text_primary"),
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            brand_panel,
            text="Un coffre clair.\nUne sécurité sous contrôle.",
            font=FONTS["heading_lg"],
            text_color=theme.get("text_primary"),
            justify="left",
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_panel,
            text="Tes identifiants restent chiffrés sur cet appareil, "
                 "et accessibles uniquement après déverrouillage.",
            font=FONTS["body_lg"],
            text_color=theme.get("text_secondary"),
            wraplength=350,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(14, 0))

        ctk.CTkLabel(
            brand_panel,
            text="Protection locale · Chiffrement AES-256-GCM",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
        ).pack(anchor="w", side="bottom", pady=(20, 4))
        
        # ── Sous-titre ──
        if self.is_first:
            subtitle = "Crée ton mot de passe maître"
            description = "Il protégera tous les accès enregistrés dans ton coffre."
        else:
            subtitle = "Content de te revoir"
            description = "Saisis ton mot de passe maître pour ouvrir le coffre."

        center_frame = ctk.CTkFrame(
            shell,
            fg_color=theme.get("bg_secondary"),
            corner_radius=DIMENSIONS["corner_radius_lg"],
            border_width=1,
            border_color=theme.get("border"),
        )
        center_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        center_frame.grid_columnconfigure(0, weight=1)

        form_content = ctk.CTkFrame(center_frame, fg_color="transparent")
        form_content.place(
            relx=0.5,
            rely=0.48,
            anchor="center",
            relwidth=0.86,
        )
        
        ctk.CTkLabel(
            form_content,
            text=subtitle,
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))
        
        ctk.CTkLabel(
            form_content,
            text=description,
            font=FONTS["body_sm"],
            text_color=theme.get("text_secondary"),
            anchor="w",
        ).pack(fill="x", pady=(0, 22))
        
        form_inner = ctk.CTkFrame(form_content, fg_color="transparent")
        form_inner.pack(fill="x")
        
        # ── Champ mot de passe ──
        ctk.CTkLabel(
            form_inner,
            text="Mot de passe maître",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))
        
        self.password_entry = ctk.CTkEntry(
            form_inner,
            placeholder_text="••••••••••••",
            font=FONTS["body"],
            width=320,
            show="•",
            **entry_style(),
        )
        self.password_entry.pack(pady=(0, 4))
        bind_entry_focus(self.password_entry)
        self.password_entry.bind("<Return>", self._on_submit)
        
        # ── Champ confirmation (uniquement au premier lancement) ──
        if self.is_first:
            ctk.CTkLabel(
                form_inner,
                text="",
                font=FONTS["caption"],
                height=8,
            ).pack()
            
            ctk.CTkLabel(
                form_inner,
                text="Confirme le mot de passe",
                font=FONTS["body_sm_bold"],
                text_color=theme.get("text_secondary"),
                anchor="w",
            ).pack(anchor="w", pady=(0, 6))
            
            self.confirm_entry = ctk.CTkEntry(
                form_inner,
                placeholder_text="••••••••••••",
                font=FONTS["body"],
                width=320,
                show="•",
                **entry_style(),
            )
            self.confirm_entry.pack(pady=(0, 4))
            bind_entry_focus(self.confirm_entry)
            self.confirm_entry.bind("<Return>", self._on_submit)
        
        # ── Message d'erreur (caché par défaut) ──
        self.error_label = ctk.CTkLabel(
            form_inner,
            text="",
            font=FONTS["body_sm"],
            text_color=theme.get("error"),
            height=20,
        )
        self.error_label.pack(pady=(8, 0))
        
        # ── Bouton de validation ──
        btn_text = "Créer mon coffre-fort" if self.is_first else "Déverrouiller"
        
        self.submit_btn = ctk.CTkButton(
            form_inner,
            text=btn_text,
            font=FONTS["body_bold"],
            width=320,
            **button_style("primary", height=48, corner_radius=DIMENSIONS["corner_radius"]),
            command=self._on_submit,
        )
        self.submit_btn.pack(pady=(16, 0))
        
        # ── Toggle afficher/masquer le mot de passe ──
        self.show_password_var = ctk.BooleanVar(value=False)
        show_pwd_check = ctk.CTkCheckBox(
            form_inner,
            text="Afficher le mot de passe",
            font=FONTS["body_sm"],
            text_color=theme.get("text_muted"),
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            border_color=theme.get("border_light"),
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
        )
        show_pwd_check.pack(pady=(14, 0))
        
        # Focus sur le champ mot de passe
        self._schedule_after(100, lambda: self.password_entry.focus_set())
    
    def _toggle_password_visibility(self):
        show_char = "" if self.show_password_var.get() else "•"
        self.password_entry.configure(show=show_char)
        if self.is_first and hasattr(self, 'confirm_entry'):
            self.confirm_entry.configure(show=show_char)
    
    def _on_submit(self, event=None):
        password = self.password_entry.get().strip()
        
        # Validation
        if not password:
            self._show_error("Entre un mot de passe")
            return
        
        if len(password) < 4:
            self._show_error("Minimum 4 caractères")
            return
        
        if self.is_first:
            # Mode création
            confirm = self.confirm_entry.get().strip()
            if password != confirm:
                self._show_error("Les mots de passe ne correspondent pas")
                return
            
            self._create_master_password(password)
        else:
            # Mode déverrouillage
            self._verify_password(password)
    
    def _create_master_password(self, password: str):
        """Crée le mot de passe maître pour la première fois."""
        # Générer un sel aléatoire
        salt = generate_salt()
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        
        # Créer le hash de vérification
        verification_hash = create_verification_hash(password, salt)
        
        # Sauvegarder dans la base
        save_master_config(salt_b64, verification_hash)
        
        # Créer les catégories par défaut
        create_default_categories()
        
        # Dériver la clé de chiffrement
        encryption_key = derive_key(password, salt)
        
        # Déverrouiller l'app
        if self.on_unlock:
            self.on_unlock(encryption_key)
    
    def _verify_password(self, password: str):
        """Vérifie le mot de passe maître."""
        salt_b64, stored_hash = get_master_config()
        
        if not salt_b64 or not stored_hash:
            self._show_error("Erreur de configuration")
            return
        
        salt = base64.b64decode(salt_b64.encode('utf-8'))
        
        if verify_master_password(password, salt, stored_hash):
            # Mot de passe correct !
            encryption_key = derive_key(password, salt)
            if self.on_unlock:
                self.on_unlock(encryption_key)
        else:
            self._show_error("Mot de passe incorrect")
            self.password_entry.delete(0, "end")
            self.password_entry.focus_set()
    
    def _show_error(self, message: str):
        """Affiche un message d'erreur rouge."""
        self.error_label.configure(text=message)
        # Reset après 3 secondes
        self._schedule_after(3000, lambda: self.error_label.configure(text=""))
