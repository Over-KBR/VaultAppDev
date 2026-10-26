"""
Page Paramètres — VaultApp V2.

Permet de :
- Changer le mot de passe maître
- Configurer la durée de verrouillage automatique
- Changer le thème par défaut
- Exporter / importer le coffre (.vault)
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from src.ui.theme import theme, FONTS, DIMENSIONS
from src import database as db


class SettingsScreen(ctk.CTkToplevel):
    """Fenêtre de paramètres."""

    def __init__(self, parent, encryption_key: bytes, on_master_password_changed=None,
                 on_theme_changed=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.encryption_key = encryption_key
        self.on_master_password_changed = on_master_password_changed
        self.on_theme_changed = on_theme_changed

        self.title("Paramètres")
        self.geometry("520x640")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg_dialog"))

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 520) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 640) // 2
        self.geometry(f"+{x}+{y}")

        self.transient(parent)
        self.grab_set()

        self._build()

    # ──────────────────────────────────────────────────────────
    # Construction
    # ──────────────────────────────────────────────────────────

    def _build(self):
        ctk.CTkLabel(
            self, text="⚙️  Paramètres",
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
        ).pack(anchor="w", padx=28, pady=(24, 20))

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
        )
        scroll.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        # ── Sécurité ──
        self._section(scroll, "🔒 Sécurité")
        self._build_lock_timer(scroll)
        self._build_change_password(scroll)

        # ── Apparence ──
        self._section(scroll, "🎨 Apparence")
        self._build_theme(scroll)

        # ── Données ──
        self._section(scroll, "💾 Données")
        self._build_export_import(scroll)

        # Bouton fermer
        ctk.CTkButton(
            self, text="Fermer",
            font=FONTS["body"],
            fg_color=theme.get("bg_tertiary"),
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_primary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["button_height"],
            command=self.destroy,
        ).pack(padx=28, pady=(0, 24), anchor="e")

    def _section(self, parent, title: str):
        """Titre de section."""
        ctk.CTkLabel(
            parent, text=title,
            font=FONTS["body_bold"],
            text_color=theme.get("text_secondary"),
            anchor="w",
        ).pack(anchor="w", pady=(16, 6))
        ctk.CTkFrame(parent, fg_color=theme.get("border"), height=1).pack(fill="x", pady=(0, 12))

    def _build_lock_timer(self, parent):
        """Durée de verrouillage automatique."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            frame, text="Verrouillage automatique",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_primary"),
            anchor="w",
        ).pack(side="left")

        saved = db.get_setting("auto_lock_minutes", "5")
        options = ["Jamais", "1 min", "5 min", "10 min", "15 min", "30 min"]
        # Reconstruire la valeur affichée
        try:
            mins = int(saved)
            if mins == 0:
                current = "Jamais"
            else:
                current = f"{mins} min" if f"{mins} min" in options else "5 min"
        except ValueError:
            current = "5 min"

        self._lock_var = ctk.StringVar(value=current)
        ctk.CTkOptionMenu(
            frame,
            variable=self._lock_var,
            values=options,
            font=FONTS["body_sm"],
            fg_color=theme.get("bg_input"),
            button_color=theme.get("bg_tertiary"),
            button_hover_color=theme.get("bg_hover"),
            dropdown_fg_color=theme.get("bg_secondary"),
            dropdown_hover_color=theme.get("bg_hover"),
            dropdown_text_color=theme.get("text_primary"),
            text_color=theme.get("text_primary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=36, width=120,
            command=self._save_lock_timer,
        ).pack(side="right")

    def _save_lock_timer(self, value: str):
        if value == "Jamais":
            db.set_setting("auto_lock_minutes", "0")
        else:
            try:
                mins = int(value.split()[0])
                db.set_setting("auto_lock_minutes", str(mins))
            except ValueError:
                pass

    def _build_change_password(self, parent):
        """Formulaire de changement du mot de passe maître."""
        frame = ctk.CTkFrame(
            parent,
            fg_color=theme.get("bg_secondary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            border_width=1, border_color=theme.get("border"),
        )
        frame.pack(fill="x", pady=(0, 14))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            inner, text="Changer le mot de passe maître",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_primary"),
        ).pack(anchor="w", pady=(0, 10))

        def _entry(placeholder):
            e = ctk.CTkEntry(
                inner,
                placeholder_text=placeholder,
                font=FONTS["body_sm"],
                fg_color=theme.get("bg_input"),
                border_color=theme.get("border"),
                text_color=theme.get("text_primary"),
                placeholder_text_color=theme.get("text_muted"),
                corner_radius=DIMENSIONS["corner_radius_sm"],
                height=38, show="•",
            )
            e.pack(fill="x", pady=4)
            return e

        self._old_pwd_entry = _entry("Mot de passe actuel")
        self._new_pwd_entry = _entry("Nouveau mot de passe")
        self._confirm_pwd_entry = _entry("Confirmer le nouveau mot de passe")

        self._change_pwd_error = ctk.CTkLabel(
            inner, text="", font=FONTS["caption"],
            text_color=theme.get("error"),
        )
        self._change_pwd_error.pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            inner, text="Changer le mot de passe",
            font=FONTS["body_sm_bold"],
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text_on_accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=36,
            command=self._do_change_password,
        ).pack(anchor="e", pady=(8, 0))

    def _do_change_password(self):
        import base64
        from src.crypto import (verify_master_password, generate_salt,
                                 derive_key, create_verification_hash)

        old_pwd = self._old_pwd_entry.get()
        new_pwd = self._new_pwd_entry.get()
        confirm = self._confirm_pwd_entry.get()

        def _err(msg):
            self._change_pwd_error.configure(text=f"⚠️ {msg}")
            self.after(4000, lambda: self._change_pwd_error.configure(text=""))

        if not old_pwd or not new_pwd or not confirm:
            return _err("Tous les champs sont obligatoires")
        if new_pwd != confirm:
            return _err("Les nouveaux mots de passe ne correspondent pas")
        if len(new_pwd) < 4:
            return _err("Minimum 4 caractères")

        # Vérifier l'ancien mot de passe
        salt_b64, stored_hash = db.get_master_config()
        salt = base64.b64decode(salt_b64.encode())
        if not verify_master_password(old_pwd, salt, stored_hash):
            return _err("Mot de passe actuel incorrect")

        # Générer un nouveau sel et re-chiffrer
        new_salt = generate_salt()
        new_hash = create_verification_hash(new_pwd, new_salt)
        new_key = derive_key(new_pwd, new_salt)

        try:
            db.change_master_password(new_pwd, new_salt, new_hash,
                                      self.encryption_key, new_key)
        except Exception as e:
            return _err(f"Erreur : {e}")

        self._old_pwd_entry.delete(0, "end")
        self._new_pwd_entry.delete(0, "end")
        self._confirm_pwd_entry.delete(0, "end")

        messagebox.showinfo(
            "Succès",
            "Mot de passe maître changé.\nL'application va se verrouiller.",
        )
        if self.on_master_password_changed:
            self.on_master_password_changed(new_key)
        self.destroy()

    def _build_theme(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            frame, text="Thème par défaut",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_primary"),
        ).pack(side="left")

        import customtkinter as ctk2
        current_mode = ctk2.get_appearance_mode()
        saved = db.get_setting("default_theme", current_mode)

        self._theme_var = ctk.StringVar(value=saved)
        ctk.CTkOptionMenu(
            frame,
            variable=self._theme_var,
            values=["dark", "light"],
            font=FONTS["body_sm"],
            fg_color=theme.get("bg_input"),
            button_color=theme.get("bg_tertiary"),
            button_hover_color=theme.get("bg_hover"),
            dropdown_fg_color=theme.get("bg_secondary"),
            dropdown_hover_color=theme.get("bg_hover"),
            dropdown_text_color=theme.get("text_primary"),
            text_color=theme.get("text_primary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=36, width=120,
            command=self._save_theme,
        ).pack(side="right")

    def _save_theme(self, value: str):
        db.set_setting("default_theme", value)
        import customtkinter as ctk2
        if value == "system":
            value = "dark"
            db.set_setting("default_theme", "dark")
            self._theme_var.set("dark")
        ctk2.set_appearance_mode(value)
        if self.on_theme_changed:
            self.on_theme_changed()

    def _build_export_import(self, parent):
        """Export / import du coffre en fichier .vault chiffré."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(
            btn_frame, text="⬆️  Exporter le coffre (.vault)",
            font=FONTS["body_sm_bold"],
            fg_color=theme.get("bg_tertiary"),
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_primary"),
            border_width=1, border_color=theme.get("border"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=38,
            command=self._export_vault,
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            btn_frame, text="⬇️  Importer un coffre (.vault)",
            font=FONTS["body_sm_bold"],
            fg_color=theme.get("bg_tertiary"),
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_primary"),
            border_width=1, border_color=theme.get("border"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=38,
            command=self._import_vault,
        ).pack(fill="x")

        ctk.CTkLabel(
            parent,
            text="Le fichier .vault est chiffré avec ton mot de passe maître.",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

    def _export_vault(self):
        from src.vault_io import export_vault
        path = filedialog.asksaveasfilename(
            defaultextension=".vault",
            filetypes=[("VaultApp backup", "*.vault")],
            title="Exporter le coffre",
        )
        if not path:
            return
        try:
            export_vault(path, self.encryption_key)
            messagebox.showinfo("Export réussi", f"Coffre exporté vers :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur d'export", str(e))

    def _import_vault(self):
        from src.vault_io import import_vault
        path = filedialog.askopenfilename(
            filetypes=[("VaultApp backup", "*.vault")],
            title="Importer un coffre",
        )
        if not path:
            return
        confirm = messagebox.askyesno(
            "Importer",
            "L'import remplacera tous les comptes et catégories actuels.\n\nContinuer ?",
            icon="warning",
        )
        if not confirm:
            return
        try:
            import_vault(path, self.encryption_key)
            messagebox.showinfo("Import réussi", "Coffre importé avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur d'import", str(e))
