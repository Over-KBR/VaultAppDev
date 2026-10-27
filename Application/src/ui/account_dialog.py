"""
Dialogue d'ajout / modification d'un compte — VaultApp V2.

Nouveautés V2 :
- Indicateur de force du mot de passe (barre colorée + label)
- Bouton générateur intégré (ouvre GeneratorPopup)
- Historique des mots de passe (3 dernières versions)
- Option "générer automatiquement" à la création
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, List
from src.ui.after_callbacks import AfterCallbackMixin
from src.ui.theme import (
    theme,
    FONTS,
    DIMENSIONS,
    bind_entry_focus,
    button_style,
    entry_style,
)
from src.ui.icons import IconButton
from src.models import Account, Category
from src.strength import analyze_password
from src.generator import generate_password


class AccountDialog(AfterCallbackMixin, ctk.CTkToplevel):
    """Dialogue pour ajouter ou modifier un compte."""

    def __init__(self, parent, categories: List[Category],
                 account: Optional[Account] = None, on_save=None,
                 encryption_key: bytes = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._init_after_callbacks()

        self.account = account
        self.categories = categories
        self.on_save = on_save
        self.encryption_key = encryption_key
        self.result = None

        # Configuration de la fenêtre
        self.title("Modifier le compte" if account else "Nouveau compte")
        self.geometry("500x680")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg_dialog"))

        # Centrer
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 680) // 2
        self.geometry(f"+{x}+{y}")

        self.transient(parent)
        self.grab_set()

        self._build()
        self._schedule_after(100, lambda: self.name_entry.focus_set())

    def destroy(self):
        self._cancel_after_callbacks()
        super().destroy()

    # ──────────────────────────────────────────────────────────
    # Construction de l'UI
    # ──────────────────────────────────────────────────────────

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 16))

        title_text = "Modifier le compte" if self.account else "Nouveau compte"
        ctk.CTkLabel(
            header, text=title_text,
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
        ).pack(anchor="w")

        # Formulaire scrollable
        form = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
        )
        form.pack(fill="both", expand=True, padx=28, pady=(0, 8))

        # ── Nom du service ──
        self.name_entry = self._create_field(
            form, "Nom du service *", "Ex : Netflix, Gmail, Steam...",
            self.account.name if self.account else "",
        )

        # ── Login ──
        self.login_entry = self._create_field(
            form, "Login / email", "Ex : email@gmail.com",
            self.account.login if self.account else "",
        )

        # ── Mot de passe ──
        self._build_password_section(form)

        # ── Vérification en deux étapes ──
        self._build_totp_section(form)

        # ── URL ──
        self.url_entry = self._create_field(
            form, "URL du site", "Ex : https://netflix.com",
            self.account.url if self.account else "",
        )

        # ── Catégorie ──
        self._build_category_section(form)

        # ── Notes ──
        self._build_notes_section(form)

        # ── Historique (edition uniquement) ──
        if self.account and self.encryption_key:
            self._build_history_section(form)

        # ── Boutons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=28, pady=(8, 24))

        ctk.CTkButton(
            btn_frame, text="Annuler",
            font=FONTS["body"],
            width=120,
            **button_style("secondary", height=DIMENSIONS["button_height"]),
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Sauvegarder",
            font=FONTS["body_bold"],
            width=160,
            **button_style("primary", height=DIMENSIONS["button_height"]),
            command=self._on_save,
        ).pack(side="right")

    def _build_password_section(self, parent):
        pwd_frame = ctk.CTkFrame(parent, fg_color="transparent")
        pwd_frame.pack(fill="x", pady=(0, 4))

        # Label + bouton générateur
        label_row = ctk.CTkFrame(pwd_frame, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            label_row, text="Mot de passe",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(side="left")

        ctk.CTkButton(
            label_row, text="Générer",
            font=FONTS["caption"],
            fg_color=theme.get("accent_light"),
            hover_color=theme.get("accent_glow"),
            text_color=theme.get("accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=28, width=84,
            command=self._open_generator,
        ).pack(side="right")

        # Champ + toggle visibilité
        pwd_input_row = ctk.CTkFrame(pwd_frame, fg_color="transparent")
        pwd_input_row.pack(fill="x")

        self.password_entry = ctk.CTkEntry(
            pwd_input_row,
            placeholder_text="••••••••",
            font=FONTS["mono"],
            show="•",
            **entry_style(),
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        bind_entry_focus(self.password_entry)

        if self.account and self.account.password:
            self.password_entry.insert(0, self.account.password)

        self._pwd_visible = False
        self.toggle_pwd_btn = IconButton(
            pwd_input_row,
            "eye",
            command=self._toggle_password,
            color="text_secondary",
            background="bg_tertiary",
            width=42, height=DIMENSIONS["input_height"],
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color=theme.get("bg_tertiary"),
            hover_color=theme.get("bg_hover"),
        )
        self.toggle_pwd_btn.button.accessible_name = "Afficher le mot de passe"
        self.toggle_pwd_btn.pack(side="right")

        # ── Barre de force ──
        strength_frame = ctk.CTkFrame(parent, fg_color="transparent")
        strength_frame.pack(fill="x", pady=(6, 14))

        # Barre colorée (5 segments)
        bar_row = ctk.CTkFrame(strength_frame, fg_color="transparent")
        bar_row.pack(fill="x")

        self._strength_segments = []
        for _ in range(5):
            seg = ctk.CTkFrame(
                bar_row,
                height=5,
                corner_radius=3,
                fg_color=theme.get("border"),
            )
            seg.pack(side="left", fill="x", expand=True, padx=2)
            self._strength_segments.append(seg)

        # Label force + temps de crack
        info_row = ctk.CTkFrame(strength_frame, fg_color="transparent")
        info_row.pack(fill="x", pady=(4, 0))

        self._strength_label = ctk.CTkLabel(
            info_row, text="",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
        )
        self._strength_label.pack(side="left")

        self._crack_label = ctk.CTkLabel(
            info_row, text="",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="e",
        )
        self._crack_label.pack(side="right")

        # Suggestion zxcvbn
        self._suggestion_label = ctk.CTkLabel(
            strength_frame, text="",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
            wraplength=380,
        )
        self._suggestion_label.pack(anchor="w", pady=(2, 0))

        # Bind pour mise à jour live
        self.password_entry.bind("<KeyRelease>", self._update_strength)
        # Initialiser si édition
        if self.account and self.account.password:
            self._schedule_after(50, self._update_strength)

    def _build_totp_section(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            frame,
            text="Secret TOTP (facultatif)",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 6))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")
        self.totp_entry = ctk.CTkEntry(
            row,
            placeholder_text="Clé Base32 fournie par le site",
            font=FONTS["mono"],
            show="•",
            **entry_style(),
        )
        self.totp_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        bind_entry_focus(self.totp_entry)
        if self.account and self.account.totp_secret:
            self.totp_entry.insert(0, self.account.totp_secret)

        self._totp_visible = False
        self._totp_toggle_btn = IconButton(
            row,
            "eye",
            command=self._toggle_totp_secret,
            color="text_secondary",
            background="bg_tertiary",
            width=42,
            height=DIMENSIONS["input_height"],
            corner_radius=DIMENSIONS["corner_radius_sm"],
            fg_color=theme.get("bg_tertiary"),
            hover_color=theme.get("bg_hover"),
        )
        self._totp_toggle_btn.button.accessible_name = "Afficher la clé de vérification"
        self._totp_toggle_btn.pack(side="right")
        ctk.CTkLabel(
            frame,
            text=(
                "Secret TOTP illisible : entre une nouvelle clé valide avant de sauvegarder."
                if self.account and self.account.totp_secret_error
                else "VaultApp le chiffre dans le coffre ; aucun service externe n'est utilisé."
            ),
            font=FONTS["caption"],
            text_color=(
                theme.get("error")
                if self.account and self.account.totp_secret_error
                else theme.get("text_muted")
            ),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

    def _toggle_totp_secret(self):
        self._totp_visible = not self._totp_visible
        self.totp_entry.configure(show="" if self._totp_visible else "•")
        self._totp_toggle_btn.icon.name = "eye_off" if self._totp_visible else "eye"
        self._totp_toggle_btn.icon.refresh()

    def _build_category_section(self, parent):
        cat_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cat_frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            cat_frame, text="Catégorie",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 6))

        cat_options = ["Sans catégorie"] + [c.name for c in self.categories]

        current_cat = "Sans catégorie"
        if self.account and self.account.category_id:
            for c in self.categories:
                if c.id == self.account.category_id:
                    current_cat = c.name
                    break

        self.category_var = ctk.StringVar(value=current_cat)
        self.category_menu = ctk.CTkOptionMenu(
            cat_frame,
            variable=self.category_var,
            values=cat_options,
            font=FONTS["body"],
            fg_color=theme.get("bg_input"),
            button_color=theme.get("bg_tertiary"),
            button_hover_color=theme.get("bg_hover"),
            dropdown_fg_color=theme.get("bg_secondary"),
            dropdown_hover_color=theme.get("bg_hover"),
            dropdown_text_color=theme.get("text_primary"),
            text_color=theme.get("text_primary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["input_height"],
        )
        self.category_menu.pack(fill="x")

    def _build_notes_section(self, parent):
        notes_frame = ctk.CTkFrame(parent, fg_color="transparent")
        notes_frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            notes_frame, text="Notes",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 6))

        self.notes_text = ctk.CTkTextbox(
            notes_frame,
            font=FONTS["body_sm"],
            fg_color=theme.get("bg_input"),
            border_color=theme.get("border"),
            text_color=theme.get("text_primary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=80, border_width=1,
        )
        self.notes_text.pack(fill="x")

        if self.account and self.account.notes:
            self.notes_text.insert("1.0", self.account.notes)

    def _build_history_section(self, parent):
        """Affiche les 3 derniers mots de passe (masqués)."""
        from src.history import get_password_history
        history = get_password_history(self.account.id, self.encryption_key)
        if not history:
            return

        hist_frame = ctk.CTkFrame(parent, fg_color="transparent")
        hist_frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            hist_frame, text="Historique des mots de passe",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 8))

        for entry in history:
            row = ctk.CTkFrame(
                hist_frame,
                fg_color=theme.get("bg_input"),
                corner_radius=DIMENSIONS["corner_radius_sm"],
            )
            row.pack(fill="x", pady=2)

            self._history_visible = {}

            pwd_label = ctk.CTkLabel(
                row, text="••••••••••••",
                font=FONTS["mono"],
                text_color=theme.get("text_muted"),
                anchor="w",
            )
            pwd_label.pack(side="left", padx=12, pady=8, fill="x", expand=True)

            date_label = ctk.CTkLabel(
                row,
                text=entry["changed_at"][:16] if entry["changed_at"] else "",
                font=FONTS["caption"],
                text_color=theme.get("text_muted"),
                anchor="e",
            )
            date_label.pack(side="right", padx=(0, 8))

            # Toggle afficher/masquer
            visible = [False]
            def _toggle(lbl=pwd_label, p=entry["password"], v=visible):
                v[0] = not v[0]
                lbl.configure(text=p if v[0] else "••••••••••••")
                eye_button.icon.name = "eye_off" if v[0] else "eye"
                eye_button.icon.refresh()

            eye_button = IconButton(
                row,
                "eye",
                command=_toggle,
                color="text_muted",
                background="bg_input",
                width=36, height=36,
                fg_color="transparent",
                hover_color=theme.get("bg_hover"),
            )
            eye_button.button.accessible_name = "Afficher une ancienne valeur"
            eye_button.pack(side="right", padx=2)

    # ──────────────────────────────────────────────────────────
    # Indicateur de force
    # ──────────────────────────────────────────────────────────

    def _update_strength(self, event=None):
        pwd = self.password_entry.get()
        result = analyze_password(pwd)

        active_segments = round(result["fraction"] * 5) if result["score"] >= 0 else 0
        color = result["color"]

        for i, seg in enumerate(self._strength_segments):
            seg.configure(fg_color=color if i < active_segments else theme.get("border"))

        if result["label"]:
            self._strength_label.configure(
                text=f"Force : {result['label']}",
                text_color=color,
            )
            crack = f"Crack offline : {result['crack_time']}" if result["crack_time"] else ""
            self._crack_label.configure(text=crack)
        else:
            self._strength_label.configure(text="")
            self._crack_label.configure(text="")

        suggestion = result["suggestions"][0] if result["suggestions"] else ""
        self._suggestion_label.configure(text=suggestion)

    # ──────────────────────────────────────────────────────────
    # Générateur intégré
    # ──────────────────────────────────────────────────────────

    def _open_generator(self):
        GeneratorPopup(self, on_use=self._use_generated_password)

    def _use_generated_password(self, password: str):
        self.password_entry.configure(show="")
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, password)
        self._pwd_visible = True
        self.toggle_pwd_btn.icon.name = "eye_off"
        self.toggle_pwd_btn.icon.refresh()
        self.toggle_pwd_btn.button.accessible_name = "Masquer le mot de passe"
        self._update_strength()

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def _create_field(self, parent, label, placeholder, value="") -> ctk.CTkEntry:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            frame, text=label,
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 6))

        entry = ctk.CTkEntry(
            frame,
            placeholder_text=placeholder,
            font=FONTS["body"],
            **entry_style(),
        )
        entry.pack(fill="x")
        bind_entry_focus(entry)
        if value:
            entry.insert(0, value)
        return entry

    def _toggle_password(self):
        self._pwd_visible = not self._pwd_visible
        self.password_entry.configure(show="" if self._pwd_visible else "•")
        self.toggle_pwd_btn.icon.name = "eye_off" if self._pwd_visible else "eye"
        self.toggle_pwd_btn.icon.refresh()
        self.toggle_pwd_btn.button.accessible_name = (
            "Masquer le mot de passe"
            if self._pwd_visible
            else "Afficher le mot de passe"
        )

    def _get_selected_category_id(self) -> Optional[int]:
        selected = self.category_var.get()
        if selected == "Sans catégorie":
            return None
        for cat in self.categories:
            if cat.name == selected:
                return cat.id
        return None

    def _on_save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=theme.get("error"))
            self._schedule_after(
                2000,
                lambda: self.name_entry.configure(border_color=theme.get("border")),
            )
            return

        from src.totp import normalize_totp_secret
        try:
            totp_secret = normalize_totp_secret(self.totp_entry.get())
        except ValueError as exc:
            messagebox.showerror("Secret TOTP invalide", str(exc), parent=self)
            return
        if self.account and self.account.totp_secret_error and not totp_secret:
            messagebox.showerror(
                "Secret TOTP illisible",
                "Entre une nouvelle clé TOTP valide avant de sauvegarder ce compte.",
                parent=self,
            )
            return

        self.result = {
            "name": name,
            "login": self.login_entry.get().strip(),
            "password": self.password_entry.get(),
            "url": self.url_entry.get().strip(),
            "notes": self.notes_text.get("1.0", "end-1c").strip(),
            "category_id": self._get_selected_category_id(),
            "totp_secret": totp_secret,
        }
        if self.on_save:
            self.on_save(self.result)
        self.destroy()


# ══════════════════════════════════════════════════════════════
# Popup Générateur de mot de passe
# ══════════════════════════════════════════════════════════════

class GeneratorPopup(ctk.CTkToplevel):
    """Popup générateur de mot de passe avec options en temps réel."""

    def __init__(self, parent, on_use=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_use = on_use

        self.title("Générateur de mot de passe")
        self.geometry("420x460")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg_dialog"))

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 460) // 2
        self.geometry(f"+{x}+{y}")
        self.transient(parent)
        self.grab_set()

        # Options
        self._length = ctk.IntVar(value=16)
        self._uppercase = ctk.BooleanVar(value=True)
        self._lowercase = ctk.BooleanVar(value=True)
        self._digits = ctk.BooleanVar(value=True)
        self._symbols = ctk.BooleanVar(value=True)

        self._build()
        self._regenerate()

    def _build(self):
        pad = dict(padx=24)

        ctk.CTkLabel(
            self, text="Générateur de mot de passe",
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
        ).pack(anchor="w", pady=(24, 16), **pad)

        # ── Aperçu mot de passe ──
        preview_frame = ctk.CTkFrame(
            self,
            fg_color=theme.get("bg_input"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            border_width=1, border_color=theme.get("border"),
            height=52,
        )
        preview_frame.pack(fill="x", **pad)
        preview_frame.pack_propagate(False)

        inner = ctk.CTkFrame(preview_frame, fg_color="transparent")
        inner.place(relx=0, rely=0.5, anchor="w", x=12, relwidth=1)

        self._preview_label = ctk.CTkLabel(
            inner, text="",
            font=FONTS["mono"],
            text_color=theme.get("text_primary"),
            anchor="w",
        )
        self._preview_label.pack(side="left", fill="x", expand=True)

        copy_button = IconButton(
            inner,
            "copy",
            command=self._copy_password,
            color="text_secondary",
            background="bg_input",
            width=34, height=34,
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
        )
        copy_button.pack(side="right", padx=(0, 8))

        # ── Barre de force ──
        str_frame = ctk.CTkFrame(self, fg_color="transparent")
        str_frame.pack(fill="x", pady=(8, 0), **pad)

        bar_row = ctk.CTkFrame(str_frame, fg_color="transparent")
        bar_row.pack(fill="x")
        self._segs = []
        for _ in range(5):
            s = ctk.CTkFrame(bar_row, height=4, corner_radius=2, fg_color=theme.get("border"))
            s.pack(side="left", fill="x", expand=True, padx=2)
            self._segs.append(s)

        self._str_label = ctk.CTkLabel(
            str_frame, text="",
            font=FONTS["caption"],
            text_color=theme.get("text_muted"),
            anchor="w",
        )
        self._str_label.pack(anchor="w", pady=(3, 0))

        # ── Longueur ──
        len_frame = ctk.CTkFrame(self, fg_color="transparent")
        len_frame.pack(fill="x", pady=(18, 0), **pad)

        len_header = ctk.CTkFrame(len_frame, fg_color="transparent")
        len_header.pack(fill="x")
        ctk.CTkLabel(
            len_header, text="Longueur",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(side="left")
        self._len_val_label = ctk.CTkLabel(
            len_header, text="16",
            font=FONTS["body_bold"],
            text_color=theme.get("accent"),
        )
        self._len_val_label.pack(side="right")

        self._len_slider = ctk.CTkSlider(
            len_frame,
            from_=4, to=64,
            variable=self._length,
            command=self._on_length_change,
            fg_color=theme.get("border"),
            progress_color=theme.get("accent"),
            button_color=theme.get("accent"),
            button_hover_color=theme.get("accent_hover"),
        )
        self._len_slider.pack(fill="x", pady=(6, 0))

        # ── Options ──
        opts_frame = ctk.CTkFrame(self, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(18, 0), **pad)

        ctk.CTkLabel(
            opts_frame, text="Options",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 8))

        opts_grid = ctk.CTkFrame(opts_frame, fg_color="transparent")
        opts_grid.pack(fill="x")

        checks = [
            ("Majuscules (A-Z)", self._uppercase),
            ("Minuscules (a-z)", self._lowercase),
            ("Chiffres (0-9)", self._digits),
            ("Symboles (!@#...)", self._symbols),
        ]
        for i, (text, var) in enumerate(checks):
            ctk.CTkCheckBox(
                opts_grid, text=text,
                font=FONTS["body_sm"],
                text_color=theme.get("text_secondary"),
                fg_color=theme.get("accent"),
                hover_color=theme.get("accent_hover"),
                border_color=theme.get("border_light"),
                variable=var,
                command=self._regenerate,
                checkbox_width=18, checkbox_height=18,
                corner_radius=4,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 16), pady=3)

        # ── Boutons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 24), **pad)

        ctk.CTkButton(
            btn_frame, text="Régénérer",
            font=FONTS["body"],
            fg_color=theme.get("bg_tertiary"),
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_primary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["button_height"],
            command=self._regenerate,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Utiliser ce mot de passe",
            font=FONTS["body_bold"],
            **button_style("primary", height=DIMENSIONS["button_height"]),
            command=self._use,
        ).pack(side="right")

    def _on_length_change(self, val):
        length = int(float(val))
        self._len_val_label.configure(text=str(length))
        self._regenerate()

    def _regenerate(self, *_):
        try:
            pwd = generate_password(
                length=int(self._length.get()),
                use_uppercase=self._uppercase.get(),
                use_lowercase=self._lowercase.get(),
                use_digits=self._digits.get(),
                use_symbols=self._symbols.get(),
            )
        except ValueError:
            pwd = ""

        self._current_pwd = pwd
        self._preview_label.configure(text=pwd if pwd else "Sélectionne au moins une option")

        result = analyze_password(pwd)
        active = round(result["fraction"] * 5) if result["score"] >= 0 else 0
        color = result["color"]
        for i, seg in enumerate(self._segs):
            seg.configure(fg_color=color if i < active else theme.get("border"))
        self._str_label.configure(
            text=f"Force : {result['label']}" if result["label"] else "",
            text_color=color,
        )

    def _copy_password(self):
        if self._current_pwd:
            from src.clipboard import copy_to_clipboard, get_clipboard_clear_seconds
            copy_to_clipboard(
                self._current_pwd,
                clear_after_seconds=get_clipboard_clear_seconds(),
            )

    def _use(self):
        if self._current_pwd and self.on_use:
            self.on_use(self._current_pwd)
        self.destroy()
