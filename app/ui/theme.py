"""Tkinter style theme for a modern colorful desktop UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

COLORS = {
    "bg": "#0f172a",
    "surface": "#111827",
    "surface_alt": "#162033",
    "card": "#1f2937",
    "panel": "#0b1220",
    "border": "#334155",
    "text": "#e5e7eb",
    "muted": "#9ca3af",
    "accent": "#14b8a6",
    "accent_2": "#3b82f6",
    "danger": "#ef4444",
    "ok": "#22c55e",
    "warn": "#f59e0b",
}


def apply_theme(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=COLORS["bg"])

    style.configure("App.TFrame", background=COLORS["bg"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("AltSurface.TFrame", background=COLORS["surface_alt"])
    style.configure("Card.TFrame", background=COLORS["card"])
    style.configure("Panel.TFrame", background=COLORS["panel"])

    style.configure(
        "TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("SF Pro Text", 11),
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("SF Pro Display", 18, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
        font=("SF Pro Text", 10),
    )
    style.configure(
        "HeroTitle.TLabel",
        background=COLORS["card"],
        foreground=COLORS["text"],
        font=("SF Pro Display", 18, "bold"),
    )
    style.configure(
        "HeroSubtitle.TLabel",
        background=COLORS["card"],
        foreground=COLORS["muted"],
        font=("SF Pro Text", 10),
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLORS["card"],
        foreground=COLORS["muted"],
        font=("SF Pro Text", 10, "bold"),
    )
    style.configure(
        "CardValue.TLabel",
        background=COLORS["card"],
        foreground=COLORS["text"],
        font=("SF Pro Display", 24, "bold"),
    )
    style.configure(
        "CardMeta.TLabel",
        background=COLORS["card"],
        foreground=COLORS["text"],
        font=("SF Pro Text", 11),
    )
    style.configure(
        "SectionTitle.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("SF Pro Display", 12, "bold"),
    )
    style.configure(
        "Accent.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["accent"],
        font=("SF Pro Text", 10, "bold"),
    )

    style.configure(
        "TButton",
        background=COLORS["accent"],
        foreground="#04111a",
        borderwidth=0,
        focusthickness=3,
        focuscolor=COLORS["accent"],
        font=("SF Pro Text", 11, "bold"),
        padding=(10, 8),
    )
    style.map(
        "TButton",
        background=[("active", "#0d9488"), ("disabled", "#374151")],
        foreground=[("disabled", "#9ca3af")],
    )

    style.configure(
        "Secondary.TButton",
        background=COLORS["accent_2"],
        foreground="white",
        font=("SF Pro Text", 10, "bold"),
    )
    style.map("Secondary.TButton", background=[("active", "#1d4ed8")])

    style.configure(
        "Danger.TButton",
        background=COLORS["danger"],
        foreground="white",
        font=("SF Pro Text", 10, "bold"),
    )
    style.map("Danger.TButton", background=[("active", "#b91c1c")])

    style.configure(
        "TEntry",
        fieldbackground=COLORS["panel"],
        foreground=COLORS["text"],
        insertcolor=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=8,
    )

    style.configure(
        "TCombobox",
        fieldbackground=COLORS["panel"],
        foreground=COLORS["text"],
        background=COLORS["panel"],
        arrowcolor=COLORS["accent"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["panel"])],
        foreground=[("readonly", COLORS["text"])],
        selectbackground=[("readonly", COLORS["surface_alt"])],
        selectforeground=[("readonly", COLORS["text"])],
    )

    style.configure(
        "Treeview",
        background=COLORS["panel"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["panel"],
        rowheight=30,
        bordercolor=COLORS["border"],
        relief="flat",
        font=("SF Pro Text", 10),
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["panel"],
        foreground=COLORS["accent"],
        font=("SF Pro Text", 10, "bold"),
        padding=(8, 8),
    )
    style.map(
        "Treeview",
        background=[("selected", "#134e4a")],
        foreground=[("selected", COLORS["text"])],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", COLORS["surface_alt"])],
        foreground=[("active", COLORS["accent"])],
    )

    style.configure(
        "TLabelframe",
        background=COLORS["surface"],
        borderwidth=1,
        relief="solid",
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
    )
    style.configure(
        "TLabelframe.Label",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("SF Pro Display", 11, "bold"),
    )

    style.configure(
        "TNotebook",
        background=COLORS["surface"],
        borderwidth=0,
        tabmargins=[2, 5, 2, 0],
    )
    style.configure(
        "TNotebook.Tab",
        background="#0b1220",
        foreground=COLORS["muted"],
        padding=(12, 8),
        font=("SF Pro Text", 10, "bold"),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["accent_2"])],
        foreground=[("selected", "white")],
    )

    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["card"],
        troughcolor=COLORS["panel"],
        bordercolor=COLORS["border"],
        arrowcolor=COLORS["accent"],
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=COLORS["card"],
        troughcolor=COLORS["panel"],
        bordercolor=COLORS["border"],
        arrowcolor=COLORS["accent"],
    )

    return style
