import customtkinter as ctk
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set, Tuple
from src.ui.theme import theme, FONTS, DIMENSIONS, blend_colors
from src.strength import analyze_password, is_weak
from src.history import get_all_last_changed_dates
from src import database as db
from src.models import Account
from src.ui.icons import Icon, normalize_icon


def parse_sqlite_timestamp(dt_str: str) -> datetime:
    """Parse un timestamp SQLite de manière robuste."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.now()


class DashboardScreen(ctk.CTkScrollableFrame):
    """
    Tableau de bord de sécurité (Audit).
    
    Affiche le score de santé global et liste les vulnérabilités du coffre-fort :
    - Mots de passe faibles (zxcvbn)
    - Mots de passe réutilisés (doublons)
    - Mots de passe obsolètes (inchangés depuis 6 mois)
    """

    def __init__(self, parent, encryption_key: bytes, on_edit_account=None, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.get("bg_primary"),
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
            **kwargs
        )
        self.encryption_key = encryption_key
        self.on_edit_account = on_edit_account

    def refresh_data(self, accounts=None):
        """Calcule les statistiques et reconstruit toute la vue."""
        # Vider les widgets existants
        for widget in self.winfo_children():
            widget.destroy()

        # 1. Récupération et analyse des données
        if accounts is None:
            accounts = db.get_all_accounts(self.encryption_key)
        last_changed_dates = get_all_last_changed_dates()

        weak_accounts: List[Tuple[Account, dict]] = []
        password_groups: Dict[str, List[Account]] = {}
        obsolete_accounts: List[Tuple[Account, int]] = [] # (account, age_in_days)

        now_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        six_months_ago = now_naive_utc - timedelta(days=180)

        for acc in accounts:
            pwd = acc.password
            if not pwd:
                continue

            # A. Mots de passe faibles
            analysis = analyze_password(pwd)
            if analysis["score"] <= 1:
                weak_accounts.append((acc, analysis))

            # B. Mots de passe réutilisés
            password_groups.setdefault(pwd, []).append(acc)

            # C. Mots de passe obsolètes
            changed_str = last_changed_dates.get(acc.id) or acc.created_at
            if changed_str:
                changed_dt = parse_sqlite_timestamp(changed_str)
                if changed_dt < six_months_ago:
                    age_days = (now_naive_utc - changed_dt).days
                    obsolete_accounts.append((acc, age_days))

        # Filtrer pour ne garder que les groupes de réutilisation (doublons)
        duplicate_groups = {
            pwd: accs for pwd, accs in password_groups.items() if len(accs) > 1
        }
        reused_count = sum(len(accs) for accs in duplicate_groups.values())

        # 2. Calcul du Score Global
        from src.strength import calculate_vault_score
        score_percent = calculate_vault_score(accounts, last_changed_dates)
        total_accounts = len(accounts)

        # 3. Rendu Visuel
        self._build_header_score(score_percent, len(weak_accounts), reused_count, len(obsolete_accounts))

        if total_accounts == 0:
            self._build_empty_state("Aucun compte enregistré", "Ajoutez des comptes pour commencer l'audit de sécurité.")
            return

        if len(weak_accounts) == 0 and reused_count == 0 and len(obsolete_accounts) == 0:
            self._build_success_state()
            return

        # Liste des vulnérabilités
        if len(weak_accounts) > 0:
            self._build_weak_section(weak_accounts)

        if reused_count > 0:
            self._build_reused_section(duplicate_groups)

        if len(obsolete_accounts) > 0:
            self._build_obsolete_section(obsolete_accounts)

    def _build_header_score(self, score: int, weak: int, reused: int, obsolete: int):
        """Construit le bloc de score global en haut."""
        # Couleur du score
        if score >= 80:
            score_color = theme.get("success")
            status_text = "Votre coffre-fort est en bonne santé."
        elif score >= 40:
            score_color = theme.get("warning")
            status_text = "Quelques points méritent votre attention."
        else:
            score_color = theme.get("error")
            status_text = "Des actions sont nécessaires pour renforcer le coffre."

        card = ctk.CTkFrame(
            self,
            fg_color=theme.get("bg_secondary"),
            corner_radius=DIMENSIONS["corner_radius_lg"],
            border_width=1,
            border_color=theme.get("border"),
        )
        card.pack(fill="x", padx=22, pady=(20, 24))

        # Deux colonnes
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=2)

        # Colonne Gauche : Score textuel
        score_left_frame = ctk.CTkFrame(card, fg_color="transparent")
        score_left_frame.grid(row=0, column=0, padx=26, pady=24, sticky="nsew")

        ctk.CTkLabel(
            score_left_frame,
            text="Score global",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w")

        Icon(
            score_left_frame,
            "shield_check" if score >= 80 else "warning",
            size=28,
            color=score_color,
            background="bg_secondary",
        ).pack(anchor="w", pady=(10, 4))
        ctk.CTkLabel(
            score_left_frame,
            text=f"{score}%",
            font=("Segoe UI Variable Display", 46, "bold"),
            text_color=theme.get("text_primary"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            score_left_frame,
            text=status_text,
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_primary"),
            wraplength=220,
            justify="left",
        ).pack(anchor="w")

        # Colonne Droite : Barre de progression et Badges stats
        score_right_frame = ctk.CTkFrame(card, fg_color="transparent")
        score_right_frame.grid(row=0, column=1, padx=26, pady=24, sticky="nsew")

        # Barre de progression
        progress = ctk.CTkProgressBar(
            score_right_frame,
            height=10,
            corner_radius=5,
            progress_color=score_color,
            fg_color=theme.get("bg_tertiary"),
        )
        progress.pack(fill="x", pady=(12, 20))
        progress.set(score / 100)

        # Badges
        badges_frame = ctk.CTkFrame(score_right_frame, fg_color="transparent")
        badges_frame.pack(fill="x", anchor="w")

        self._add_badge(badges_frame, "warning", f"{weak} faible" + ("s" if weak > 1 else ""))
        self._add_badge(badges_frame, "copy", f"{reused} réutilisé" + ("s" if reused > 1 else ""))
        self._add_badge(badges_frame, "info", f"{obsolete} obsolète" + ("s" if obsolete > 1 else ""))

    def _add_badge(self, parent, icon: str, label: str):
        badge = ctk.CTkFrame(
            parent,
            fg_color=theme.get("bg_tertiary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=28,
        )
        badge.pack(side="left", padx=(0, 10))
        
        Icon(
            badge,
            icon,
            size=14,
            color="text_secondary",
            background="bg_tertiary",
        ).pack(side="left", padx=(8, 4), pady=2)
        lbl = ctk.CTkLabel(
            badge,
            text=label,
            font=FONTS["caption"],
            text_color=theme.get("text_primary"),
        )
        lbl.pack(side="left", padx=(0, 8), pady=2)

    def _build_weak_section(self, weak_accounts: List[Tuple[Account, dict]]):
        """Construit la liste des mots de passe faibles."""
        section = self._create_section_frame("Mots de passe faibles", f"{len(weak_accounts)} mots de passe sont trop simples et faciles à deviner.")
        
        for acc, analysis in weak_accounts:
            self._build_vulnerability_row(
                section,
                account=acc,
                badge_text=analysis["label"],
                badge_color=analysis["color"],
                desc=f"Force : {analysis['score']}/4. Suggestions : " + 
                     (", ".join(analysis["suggestions"]) if analysis["suggestions"] else "Rendre le mot de passe plus long et varié.")
            )

    def _build_reused_section(self, duplicate_groups: Dict[str, List[Account]]):
        """Construit la liste des mots de passe réutilisés."""
        total_accounts = sum(len(accs) for accs in duplicate_groups.values())
        section = self._create_section_frame("Mots de passe réutilisés", f"Les mêmes mots de passe sont utilisés sur {total_accounts} comptes.")

        for pwd, accs in duplicate_groups.items():
            group_frame = ctk.CTkFrame(
                section,
                fg_color=theme.get("bg_secondary"),
                corner_radius=DIMENSIONS["corner_radius_sm"],
                border_width=1,
                border_color=theme.get("border"),
            )
            group_frame.pack(fill="x", pady=6, padx=8)

            header = ctk.CTkLabel(
                group_frame,
                text=f"Mot de passe répété {len(accs)} fois",
                font=FONTS["body_sm_bold"],
                text_color=theme.get("warning"),
                anchor="w",
            )
            header.pack(fill="x", padx=12, pady=(10, 6))

            for acc in accs:
                self._build_vulnerability_row(
                    group_frame,
                    account=acc,
                    badge_text="Doublon",
                    badge_color=theme.get("warning"),
                            desc=f"Identifiant : {acc.login if acc.login else 'Aucun identifiant'}",
                    padx=12,
                    pady=4
                )

    def _build_obsolete_section(self, obsolete_accounts: List[Tuple[Account, int]]):
        """Construit la liste des mots de passe obsolètes."""
        section = self._create_section_frame("Mots de passe anciens", f"{len(obsolete_accounts)} mots de passe n'ont pas été modifiés depuis plus de six mois.")

        for acc, age_days in obsolete_accounts:
            months = age_days // 30
            self._build_vulnerability_row(
                section,
                account=acc,
                badge_text=f"{months} mois",
                badge_color=theme.get("info"),
                desc=f"Dernier changement il y a {age_days} jours."
            )

    def _create_section_frame(self, title: str, subtitle: str) -> ctk.CTkFrame:
        """Crée une section stylisée avec titre et sous-titre."""
        section = ctk.CTkFrame(self, fg_color="transparent")
        section.pack(fill="x", padx=22, pady=14)

        ctk.CTkLabel(
            section,
            text=title,
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            section,
            text=subtitle,
            font=FONTS["body_sm"],
            text_color=theme.get("text_secondary"),
            anchor="w",
        ).pack(fill="x", pady=(2, 10))

        return section

    def _build_vulnerability_row(self, parent, account: Account, badge_text: str, badge_color: str, desc: str, padx=8, pady=6):
        """Construit une ligne de vulnérabilité pour un compte."""
        row = ctk.CTkFrame(
            parent,
            fg_color=theme.get("bg_secondary") if parent.cget("fg_color") == "transparent" else theme.get("bg_tertiary"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            border_width=1,
            border_color=theme.get("border"),
            height=88,
        )
        row.pack(fill="x", pady=pady, padx=padx)
        row.pack_propagate(False)

        category_icon = Icon(
            row,
            normalize_icon(account.category_icon),
            size=18,
            color=account.category_color,
            background="bg_secondary",
        )
        category_icon.pack(side="left", padx=12)

        edit_btn = ctk.CTkButton(
            row,
            text="Modifier",
            font=FONTS["body_sm_bold"],
            fg_color="transparent",
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_secondary"),
            width=90,
            height=32,
            corner_radius=DIMENSIONS["corner_radius_sm"],
            command=lambda: self._trigger_edit(account)
        )
        edit_btn.pack(side="right", padx=12, pady=16)

        # Colonne 2 : Info compte (Nom + description)
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=10)

        title_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_row.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            title_row,
            text=account.name,
            font=FONTS["body_bold"],
            text_color=theme.get("text_primary"),
            anchor="w",
        ).pack(side="left")

        # Petit badge de type de vulnérabilité
        badge = ctk.CTkFrame(
            title_row,
            fg_color=blend_colors(badge_color, theme.get("bg_secondary"), 0.12),
            corner_radius=DIMENSIONS["corner_radius_sm"],
        )
        badge.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            badge,
            text=badge_text,
            font=FONTS["caption"],
            text_color=badge_color,
        ).pack(padx=6, pady=1)

        description = ctk.CTkLabel(
            info_frame,
            text=desc,
            font=FONTS["body_sm"],
            text_color=theme.get("text_secondary"),
            anchor="w",
        )
        description.pack(anchor="w", fill="x")
        info_frame.bind(
            "<Configure>",
            lambda event: description.configure(
                wraplength=max(120, event.width - 8)
            ),
            add="+",
        )

    def _trigger_edit(self, account: Account):
        if self.on_edit_account:
            self.on_edit_account(account)

    def _build_success_state(self):
        """Affiche un écran de succès si aucune faille n'est détectée."""
        success_frame = ctk.CTkFrame(self, fg_color="transparent")
        success_frame.pack(fill="both", expand=True, pady=60)

        Icon(
            success_frame,
            "shield_check",
            size=56,
            color="success",
            background="bg_primary",
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            success_frame,
            text="Coffre parfaitement sécurisé !",
            font=FONTS["heading_sm"],
            text_color=theme.get("success"),
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            success_frame,
            text="Félicitations, tous vos mots de passe sont forts,\nuniques et ont été mis à jour récemment.",
            font=FONTS["body"],
            text_color=theme.get("text_secondary"),
            justify="center",
        ).pack()

    def _build_empty_state(self, title: str, subtitle: str):
        """Affiche un état vide."""
        empty_frame = ctk.CTkFrame(self, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, pady=60)

        Icon(
            empty_frame,
            "list",
            size=38,
            color="text_muted",
            background="bg_primary",
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            empty_frame,
            text=title,
            font=FONTS["heading_sm"],
            text_color=theme.get("text_secondary"),
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            empty_frame,
            text=subtitle,
            font=FONTS["body_sm"],
            text_color=theme.get("text_muted"),
        ).pack()
