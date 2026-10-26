"""
Écran de déverrouillage de VaultApp.

Deux modes :
1. Premier lancement → Création du mot de passe maître
2. Lancements suivants → Saisie du mot de passe maître pour déverrouiller
"""

import base64
import customtkinter as ctk
from src.ui.theme import theme, FONTS, DIMENSIONS
from src.crypto import generate_salt, derive_key, create_verification_hash, verify_master_password
from src.database import is_first_launch, save_master_config, get_master_config, init_database, create_default_categories


class LoginScreen(ctk.CTkFrame):
    """Écran de déverrouillage / création du mot de passe maître."""
    
    def __init__(self, parent, on_unlock=None, **kwargs):
        super().__init__(parent, fg_color=theme.get("bg_primary"), **kwargs)
        
        self.on_unlock = on_unlock  # Callback appelé quand le mot de passe est validé
        self.is_first = is_first_launch()
        
        self._build()
    
    def _build(self):
        # ══════════════════════════════════════════
        # Conteneur centré
        # ══════════════════════════════════════════
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # ── Logo / Icône ──
        logo_frame = ctk.CTkFrame(
            center_frame,
            fg_color=theme.get("accent_light"),
            corner_radius=24,
            width=90,
            height=90,
        )
        logo_frame.pack(pady=(0, 24))
        logo_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            logo_frame,
            text="🔐",
            font=("Segoe UI Emoji", 38),
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # ── Titre ──
        ctk.CTkLabel(
            center_frame,
            text="VaultApp",
            font=FONTS["heading_xl"],
            text_color=theme.get("text_primary"),
        ).pack(pady=(0, 4))
        
        # ── Sous-titre ──
        if self.is_first:
            subtitle = "Bienvenue ! Crée ton mot de passe maître"
            description = "Ce mot de passe protégera tous tes comptes.\nChoisis-le bien et ne l'oublie pas !"
        else:
            subtitle = "Content de te revoir !"
            description = "Entre ton mot de passe maître pour déverrouiller"
        
        ctk.CTkLabel(
            center_frame,
            text=subtitle,
            font=FONTS["body"],
            text_color=theme.get("text_secondary"),
        ).pack(pady=(0, 4))
        
        ctk.CTkLabel(
            center_frame,
            text=description,
            font=FONTS["body_sm"],
            text_color=theme.get("text_muted"),
        ).pack(pady=(0, 28))
        
        # ══════════════════════════════════════════
        # Formulaire
        # ══════════════════════════════════════════
        form_frame = ctk.CTkFrame(
            center_frame,
            fg_color=theme.get("bg_secondary"),
            corner_radius=DIMENSIONS["corner_radius_lg"],
            border_width=1,
            border_color=theme.get("border"),
        )
        form_frame.pack(padx=20)
        
        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(padx=36, pady=32)
        
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
            fg_color=theme.get("bg_input"),
            border_color=theme.get("border"),
            text_color=theme.get("text_primary"),
            placeholder_text_color=theme.get("text_muted"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["input_height"],
            width=320,
            show="•",
        )
        self.password_entry.pack(pady=(0, 4))
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
                fg_color=theme.get("bg_input"),
                border_color=theme.get("border"),
                text_color=theme.get("text_primary"),
                placeholder_text_color=theme.get("text_muted"),
                corner_radius=DIMENSIONS["corner_radius_sm"],
                height=DIMENSIONS["input_height"],
                width=320,
                show="•",
            )
            self.confirm_entry.pack(pady=(0, 4))
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
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text_on_accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["button_height"],
            width=320,
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
        self.after(100, lambda: self.password_entry.focus_set())
    
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
        self.error_label.configure(text=f"⚠️ {message}")
        # Reset après 3 secondes
        self.after(3000, lambda: self.error_label.configure(text=""))
