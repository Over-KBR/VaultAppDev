"""
Dialogue de gestion des catégories.

Permet de :
- Créer une nouvelle catégorie
- Modifier une catégorie existante
- Choisir un nom, une couleur et une icône
"""

import customtkinter as ctk
from typing import Optional
from src.ui.theme import theme, FONTS, DIMENSIONS, blend_colors
from src.models import Category, CATEGORY_ICONS, CATEGORY_COLORS


class CategoryDialog(ctk.CTkToplevel):
    """Dialogue pour créer ou modifier une catégorie."""
    
    def __init__(self, parent, category: Optional[Category] = None, 
                 on_save=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.category = category
        self.on_save = on_save
        self.selected_color = category.color if category else CATEGORY_COLORS[0]["hex"]
        self.selected_icon = category.icon if category else CATEGORY_ICONS[0]
        
        # Configuration
        self.title("Modifier la catégorie" if category else "Nouvelle catégorie")
        self.geometry("440x580")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg_dialog"))
        
        # Centrer
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 440) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 580) // 2
        self.geometry(f"+{x}+{y}")
        
        self.transient(parent)
        self.grab_set()
        
        self._build()
    
    def _build(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=theme.get("bg_dialog"))
        header.pack(fill="x", padx=28, pady=(24, 16))
        
        title_text = "✏️  Modifier la catégorie" if self.category else "📁  Nouvelle catégorie"
        ctk.CTkLabel(
            header,
            text=title_text,
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
        ).pack(anchor="w")
        
        # ── Formulaire scrollable ──
        form = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.get("bg_dialog"),
            scrollbar_button_color=theme.get("scrollbar"),
            scrollbar_button_hover_color=theme.get("scrollbar_hover"),
        )
        form.pack(fill="both", expand=True, padx=28, pady=(0, 8))
        
        # ── Aperçu en temps réel ──
        self.preview_frame = ctk.CTkFrame(
            form,
            fg_color=blend_colors(self.selected_color, theme.get("bg_dialog"), 0.12),
            corner_radius=DIMENSIONS["corner_radius"],
            height=60,
        )
        self.preview_frame.pack(fill="x", pady=(0, 18))
        self.preview_frame.pack_propagate(False)
        
        preview_inner = ctk.CTkFrame(self.preview_frame, fg_color=theme.get("bg_dialog"))
        preview_inner.place(relx=0.5, rely=0.5, anchor="center")
        
        self.preview_icon = ctk.CTkLabel(
            preview_inner,
            text=self.selected_icon,
            font=FONTS["icon_lg"],
        )
        self.preview_icon.pack(side="left", padx=(0, 10))
        
        self.preview_name = ctk.CTkLabel(
            preview_inner,
            text=self.category.name if self.category else "Ma catégorie",
            font=FONTS["heading_sm"],
            text_color=theme.get("text_primary"),
        )
        self.preview_name.pack(side="left")
        
        # ── Nom ──
        name_frame = ctk.CTkFrame(form, fg_color=theme.get("bg_dialog"))
        name_frame.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(
            name_frame,
            text="Nom de la catégorie",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 6))
        
        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Ex : Réseaux sociaux",
            font=FONTS["body"],
            fg_color=theme.get("bg_input"),
            border_color=theme.get("border"),
            text_color=theme.get("text_primary"),
            placeholder_text_color=theme.get("text_muted"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["input_height"],
        )
        self.name_entry.pack(fill="x")
        self.name_entry.bind("<KeyRelease>", self._update_preview)
        
        if self.category:
            self.name_entry.insert(0, self.category.name)
        
        # ── Sélecteur de couleur ──
        color_frame = ctk.CTkFrame(form, fg_color=theme.get("bg_dialog"))
        color_frame.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(
            color_frame,
            text="Couleur",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 8))
        
        colors_grid = ctk.CTkFrame(color_frame, fg_color=theme.get("bg_dialog"))
        colors_grid.pack(fill="x")
        
        self.color_buttons = []
        for i, color_info in enumerate(CATEGORY_COLORS):
            is_selected = color_info["hex"] == self.selected_color
            btn = ctk.CTkButton(
                colors_grid,
                text="✓" if is_selected else "",
                width=38,
                height=38,
                corner_radius=19,
                fg_color=color_info["hex"],
                hover_color=color_info["hex"],
                border_width=3 if is_selected else 0,
                border_color=theme.get("text_on_accent") if is_selected else color_info["hex"],
                text_color=theme.get("text_on_accent"),
                font=FONTS["body_bold"],
                command=lambda c=color_info["hex"]: self._select_color(c),
            )
            btn.grid(row=i // 7, column=i % 7, padx=4, pady=4)
            self.color_buttons.append((btn, color_info["hex"]))
        
        # ── Sélecteur d'icône ──
        icon_frame = ctk.CTkFrame(form, fg_color=theme.get("bg_dialog"))
        icon_frame.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(
            icon_frame,
            text="Icône",
            font=FONTS["body_sm_bold"],
            text_color=theme.get("text_secondary"),
        ).pack(anchor="w", pady=(0, 8))
        
        icons_grid = ctk.CTkFrame(icon_frame, fg_color=theme.get("bg_dialog"))
        icons_grid.pack(fill="x")
        
        self.icon_buttons = []
        cols = 8
        for i, icon in enumerate(CATEGORY_ICONS):
            is_selected = icon == self.selected_icon
            btn = ctk.CTkButton(
                icons_grid,
                text=icon,
                font=FONTS["icon_sm"],
                width=40,
                height=40,
                corner_radius=DIMENSIONS["corner_radius_sm"],
                fg_color=theme.get("accent_light") if is_selected else theme.get("bg_tertiary"),
                hover_color=theme.get("bg_hover"),
                text_color=theme.get("text_primary"),
                border_width=2 if is_selected else 0,
                border_color=theme.get("accent") if is_selected else theme.get("bg_tertiary"),
                command=lambda ic=icon: self._select_icon(ic),
            )
            btn.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            self.icon_buttons.append((btn, icon))
        
        # ── Boutons ──
        btn_frame = ctk.CTkFrame(self, fg_color=theme.get("bg_dialog"))
        btn_frame.pack(fill="x", padx=28, pady=(8, 24))
        
        ctk.CTkButton(
            btn_frame,
            text="Annuler",
            font=FONTS["body"],
            fg_color=theme.get("bg_tertiary"),
            hover_color=theme.get("bg_hover"),
            text_color=theme.get("text_secondary"),
            border_width=1,
            border_color=theme.get("border"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["button_height"],
            width=120,
            command=self.destroy,
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frame,
            text="💾  Sauvegarder",
            font=FONTS["body_bold"],
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text_on_accent"),
            corner_radius=DIMENSIONS["corner_radius_sm"],
            height=DIMENSIONS["button_height"],
            width=160,
            command=self._on_save,
        ).pack(side="right")
    
    def _select_color(self, color: str):
        self.selected_color = color
        for btn, c in self.color_buttons:
            is_sel = c == color
            btn.configure(
                text="✓" if is_sel else "",
                border_width=3 if is_sel else 0,
                border_color=theme.get("text_on_accent") if is_sel else c,
            )
        self._update_preview()
    
    def _select_icon(self, icon: str):
        self.selected_icon = icon
        for btn, ic in self.icon_buttons:
            is_sel = ic == icon
            btn.configure(
                fg_color=theme.get("accent_light") if is_sel else theme.get("bg_tertiary"),
                border_width=2 if is_sel else 0,
                border_color=theme.get("accent") if is_sel else theme.get("bg_tertiary"),
            )
        self._update_preview()
    
    def _update_preview(self, event=None):
        name = self.name_entry.get().strip() or "Ma catégorie"
        self.preview_name.configure(text=name)
        self.preview_icon.configure(text=self.selected_icon)
        self.preview_frame.configure(
            fg_color=blend_colors(self.selected_color, theme.get("bg_dialog"), 0.12)
        )
    
    def _on_save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=theme.get("error"))
            self.after(2000, lambda: self.name_entry.configure(border_color=theme.get("border")))
            return
        
        result = {
            "name": name,
            "color": self.selected_color,
            "icon": self.selected_icon,
        }
        
        if self.on_save:
            self.on_save(result)
        
        self.destroy()