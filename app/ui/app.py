"""Tkinter desktop UI for the PAMS application."""

from __future__ import annotations

import re
import tkinter as tk
from datetime import date
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Callable

from app.config import AppConfig
from app.rbac import (
    ROLE_TENANT,
    CurrentUser,
    can,
)
from app.services import PamsService
from app.ui.theme import COLORS, apply_theme


STATUS_TAG_COLORS = {
    "status_paid": COLORS["ok"],
    "status_resolved": COLORS["ok"],
    "status_closed": COLORS["ok"],
    "status_available": COLORS["ok"],
    "status_active": COLORS["ok"],
    "status_partial": COLORS["warn"],
    "status_pending": COLORS["warn"],
    "status_open": COLORS["warn"],
    "status_in_review": COLORS["warn"],
    "status_scheduled": COLORS["warn"],
    "status_in_progress": COLORS["accent_2"],
    "status_reported": COLORS["accent_2"],
    "status_maintenance": COLORS["accent_2"],
    "status_occupied": COLORS["text"],
    "status_ended": COLORS["muted"],
    "status_inactive": COLORS["muted"],
    "status_early_leave_requested": "#fbbf24",
    "status_late": "#fda4af",
}


def _normalize_tag(prefix: str, value: str | None) -> str | None:
    if not value:
        return None
    safe = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return f"{prefix}_{safe}" if safe else None


def create_treeview(
    parent: tk.Widget,
    columns: tuple[str, ...],
    specs: list[tuple[str, str, int]],
    *,
    height: int | None = None,
) -> ttk.Treeview:
    shell = ttk.Frame(parent, style="Surface.TFrame")
    shell.pack(fill="both", expand=True)
    shell.columnconfigure(0, weight=1)
    shell.rowconfigure(0, weight=1)

    tree = ttk.Treeview(shell, columns=columns, show="headings", height=height)
    vbar = ttk.Scrollbar(shell, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
    hbar = ttk.Scrollbar(shell, orient="horizontal", command=tree.xview, style="Horizontal.TScrollbar")
    tree.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vbar.grid(row=0, column=1, sticky="ns")
    hbar.grid(row=1, column=0, sticky="ew")

    for col, title, width in specs:
        tree.heading(col, text=title)
        tree.column(col, width=width, stretch=True)

    tree.tag_configure("row_even", background=COLORS["panel"])
    tree.tag_configure("row_odd", background=COLORS["surface_alt"])
    for tag_name, color in STATUS_TAG_COLORS.items():
        tree.tag_configure(tag_name, foreground=color)
    return tree


def insert_tree_row(
    tree: ttk.Treeview,
    values: tuple[Any, ...],
    *,
    status: str | None = None,
) -> None:
    stripe = "row_even" if len(tree.get_children()) % 2 == 0 else "row_odd"
    tags = [stripe]
    status_tag = _normalize_tag("status", status)
    if status_tag:
        tags.append(status_tag)
    tree.insert("", tk.END, values=values, tags=tuple(tags))


class PamsDesktopApp(tk.Tk):
    def __init__(self, service: PamsService, cfg: AppConfig) -> None:
        super().__init__()
        self.service = service
        self.cfg = cfg
        self.title(cfg.app_title)
        self.geometry("1440x900")
        self.minsize(1180, 760)
        apply_theme(self)

        self._current_user: CurrentUser | None = None
        self._current_view: tk.Widget | None = None

        self.show_login()

    def show_login(self) -> None:
        if self._current_view:
            self._current_view.destroy()
        self._current_view = LoginFrame(self, self._on_login)
        self._current_view.pack(fill="both", expand=True)

    def _on_login(self, username: str, password: str) -> None:
        try:
            user = self.service.authenticate(username, password)
        except Exception as exc:
            messagebox.showerror("Login failed", str(exc))
            return

        self._current_user = user
        if self._current_view:
            self._current_view.destroy()
        if user.role == ROLE_TENANT:
            self._current_view = TenantDashboardFrame(self, self.service, user, self._logout)
        else:
            self._current_view = MainFrame(self, self.service, user, self._logout)
        self._current_view.pack(fill="both", expand=True)

    def _logout(self) -> None:
        self._current_user = None
        self.show_login()


class LoginFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, login_callback: Callable[[str, str], None]) -> None:
        super().__init__(parent, style="App.TFrame")
        self.login_callback = login_callback

        container = ttk.Frame(self, style="Card.TFrame", padding=46)
        container.place(relx=0.5, rely=0.5, anchor="center")
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        ttk.Label(container, text="Paragon Apartment Management System", style="HeroTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )
        ttk.Label(
            container,
            text="Secure multi-city desktop platform (Tkinter + MySQL)",
            style="HeroSubtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 18))

        ttk.Label(container, text="Username", style="SectionTitle.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.username_entry = ttk.Entry(container, width=34)
        self.username_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(container, text="Password", style="SectionTitle.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.password_entry = ttk.Entry(container, width=34, show="*")
        self.password_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        ttk.Button(container, text="Sign In", command=self._submit).grid(
            row=6, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(container, text="Clear", style="Secondary.TButton", command=self._clear).grid(
            row=6, column=1, sticky="ew"
        )

        self.password_entry.bind("<Return>", lambda _: self._submit())
        self.username_entry.focus_set()

    def _submit(self) -> None:
        self.login_callback(self.username_entry.get(), self.password_entry.get())

    def _clear(self) -> None:
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)


class TenantDashboardFrame(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        service: PamsService,
        user: CurrentUser,
        logout_callback: Callable[[], None],
    ) -> None:
        super().__init__(parent, style="Surface.TFrame")
        self.service = service
        self.user = user
        self.logout_callback = logout_callback
        self.tabs: list[Any] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_header()
        self._build_summary()
        self._build_tabs()
        self.refresh_all()

    def _build_header(self) -> None:
        header = ttk.Frame(self, style="Surface.TFrame", padding=(20, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Tenant Portal", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        sub = f"Signed in: {self.user.full_name} ({self.user.username})"
        ttk.Label(header, text=sub, style="Subtitle.TLabel").grid(row=1, column=0, sticky="w")

        ttk.Button(header, text="Refresh", style="Secondary.TButton", command=self.refresh_all).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(header, text="Logout", style="Danger.TButton", command=self.logout_callback).grid(
            row=0, column=2
        )

    def _build_summary(self) -> None:
        row = ttk.Frame(self, style="Surface.TFrame", padding=(20, 0, 20, 10))
        row.grid(row=1, column=0, sticky="ew")
        row.columnconfigure(0, weight=2)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=1)

        profile_card = ttk.Frame(row, style="Card.TFrame", padding=14)
        profile_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(profile_card, text="Tenant Details", style="CardTitle.TLabel").pack(anchor="w")
        self.profile_lbl = ttk.Label(profile_card, text="Tenant details", style="CardMeta.TLabel", wraplength=520)
        self.profile_lbl.pack(anchor="w", pady=(6, 0))

        late_card = ttk.Frame(row, style="Card.TFrame", padding=14)
        late_card.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
        ttk.Label(late_card, text="Late Alerts", style="CardTitle.TLabel").pack(anchor="w")
        self.late_lbl = ttk.Label(late_card, text="0", style="CardValue.TLabel")
        self.late_lbl.pack(anchor="w", pady=(4, 0))

        out_card = ttk.Frame(row, style="Card.TFrame", padding=14)
        out_card.grid(row=0, column=2, sticky="nsew")
        ttk.Label(out_card, text="Outstanding Balance", style="CardTitle.TLabel").pack(anchor="w")
        self.outstanding_lbl = ttk.Label(out_card, text="£0.00", style="CardValue.TLabel")
        self.outstanding_lbl.pack(anchor="w", pady=(4, 0))

    def _build_tabs(self) -> None:
        panel = ttk.Frame(self, style="Surface.TFrame", padding=(20, 0, 20, 20))
        panel.grid(row=2, column=0, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(panel)
        notebook.grid(row=0, column=0, sticky="nsew")

        payments = TenantPaymentsTab(notebook, self)
        alerts = TenantAlertsTab(notebook, self)
        complaints = TenantComplaintsTab(notebook, self)
        repairs = TenantRepairsTab(notebook, self)
        charts = TenantChartsTab(notebook, self)

        self.tabs = [payments, alerts, complaints, repairs, charts]
        notebook.add(payments, text="My Payments")
        notebook.add(alerts, text="Late Alerts")
        notebook.add(complaints, text="Complaints")
        notebook.add(repairs, text="Repairs")
        notebook.add(charts, text="Charts")

    def refresh_all(self) -> None:
        profile = self.service.tenant_profile(self.user)
        payment_rows = self.service.tenant_payment_records(self.user)
        late_rows = self.service.tenant_late_alerts(self.user)

        outstanding = sum(float(r.get("outstanding") or 0) for r in payment_rows)
        tenant_name = profile.get("tenant_name", self.user.full_name)
        city_name = profile.get("city_name") or "-"
        apartment_code = profile.get("apartment_code") or "-"
        self.profile_lbl.configure(text=f"{tenant_name} | City: {city_name} | Apartment: {apartment_code}")
        self.late_lbl.configure(text=str(len(late_rows)))
        self.outstanding_lbl.configure(text=f"£{outstanding:.2f}")

        for tab in self.tabs:
            tab.refresh()


class TenantBaseTab(ttk.Frame):
    title = "Tenant"

    def __init__(self, parent: tk.Widget, dashboard: TenantDashboardFrame) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=12)
        self.dashboard = dashboard

    @property
    def service(self) -> PamsService:
        return self.dashboard.service

    @property
    def user(self) -> CurrentUser:
        return self.dashboard.user

    def refresh(self) -> None:
        pass

    def _show_error(self, exc: Exception) -> None:
        messagebox.showerror(self.title, str(exc))

    def _show_info(self, msg: str) -> None:
        messagebox.showinfo(self.title, msg)


class TenantPaymentsTab(TenantBaseTab):
    title = "My Payments"

    def __init__(self, parent: tk.Widget, dashboard: TenantDashboardFrame) -> None:
        super().__init__(parent, dashboard)

        top = ttk.Frame(self, style="Surface.TFrame")
        top.pack(fill="x")

        pay_box = ttk.LabelFrame(top, text="Make Card Payment", padding=10)
        pay_box.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.invoice_id_e = ttk.Entry(pay_box, width=10)
        self.amount_e = ttk.Entry(pay_box, width=10)
        self.paid_on_e = ttk.Entry(pay_box, width=12)
        self.card_e = ttk.Entry(pay_box, width=20)
        self.exp_e = ttk.Entry(pay_box, width=8)
        self.cvv_e = ttk.Entry(pay_box, width=6, show="*")
        self.paid_on_e.insert(0, date.today().isoformat())

        rows = [
            ("Invoice ID", self.invoice_id_e),
            ("Amount", self.amount_e),
            ("Paid On YYYY-MM-DD", self.paid_on_e),
            ("Card Number", self.card_e),
            ("Expiry MM/YY", self.exp_e),
            ("CVV", self.cvv_e),
        ]
        pay_box.columnconfigure(1, weight=1)
        for i, (label, w) in enumerate(rows):
            ttk.Label(pay_box, text=label).grid(row=i, column=0, sticky="w")
            w.grid(row=i, column=1, sticky="ew", pady=(0, 2))

        ttk.Button(pay_box, text="Pay Now", command=self._pay_now).grid(
            row=len(rows), column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        list_box = ttk.LabelFrame(self, text="My Invoices and Payments", padding=10)
        list_box.pack(fill="both", expand=True, pady=(8, 0))

        cols = ("invoice", "month", "due", "amount", "paid_total", "outstanding", "status", "apartment")
        self.tree = create_treeview(list_box, cols, [
            ("invoice", "Invoice", 90),
            ("month", "Month", 110),
            ("due", "Due Date", 110),
            ("amount", "Amount", 100),
            ("paid_total", "Paid", 100),
            ("outstanding", "Outstanding", 110),
            ("status", "Status", 100),
            ("apartment", "Property", 120),
        ])

    def _pay_now(self) -> None:
        try:
            payment_id = self.service.tenant_make_card_payment(
                self.user,
                invoice_id=int(self.invoice_id_e.get()),
                amount=self.amount_e.get(),
                paid_on=self.paid_on_e.get(),
                card_number=self.card_e.get(),
                expiry_mm_yy=self.exp_e.get(),
                cvv=self.cvv_e.get(),
            )
            self._show_info(f"Payment successful. ID: {payment_id}")
            self.dashboard.refresh_all()
        except Exception as exc:
            self._show_error(exc)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = self.service.tenant_payment_records(self.user)
        for row in rows:
            insert_tree_row(
                self.tree,
                (
                    row["invoice_id"],
                    row["billing_month"],
                    row["due_date"],
                    f"£{float(row['amount']):.2f}",
                    f"£{float(row['paid_total']):.2f}",
                    f"£{float(row['outstanding']):.2f}",
                    row["status"],
                    row["apartment_code"],
                ),
                status=str(row["status"]),
            )


class TenantAlertsTab(TenantBaseTab):
    title = "Late Alerts"

    def __init__(self, parent: tk.Widget, dashboard: TenantDashboardFrame) -> None:
        super().__init__(parent, dashboard)
        box = ttk.LabelFrame(self, text="Late Payment Alerts", padding=10)
        box.pack(fill="both", expand=True)
        cols = ("invoice", "month", "due", "amount", "status", "property")
        self.tree = create_treeview(box, cols, [
            ("invoice", "Invoice", 100),
            ("month", "Month", 120),
            ("due", "Due Date", 120),
            ("amount", "Amount", 120),
            ("status", "Status", 120),
            ("property", "Property", 140),
        ])

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = self.service.tenant_late_alerts(self.user)
        for row in rows:
            insert_tree_row(
                self.tree,
                (
                    row["invoice_id"],
                    row["billing_month"],
                    row["due_date"],
                    f"£{float(row['amount']):.2f}",
                    row["status"],
                    row["apartment_code"],
                ),
                status=str(row["status"]),
            )


class TenantComplaintsTab(TenantBaseTab):
    title = "Complaints"

    def __init__(self, parent: tk.Widget, dashboard: TenantDashboardFrame) -> None:
        super().__init__(parent, dashboard)
        box = ttk.LabelFrame(self, text="Submit Complaint", padding=10)
        box.pack(fill="x")
        box.columnconfigure(1, weight=1)

        self.title_e = ttk.Entry(box, width=28)
        self.desc_e = ttk.Entry(box, width=60)

        ttk.Label(box, text="Title").grid(row=0, column=0, sticky="w")
        self.title_e.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Label(box, text="Description").grid(row=1, column=0, sticky="w")
        self.desc_e.grid(row=1, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(box, text="Submit Complaint", command=self._submit).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _submit(self) -> None:
        try:
            complaint_id = self.service.tenant_submit_complaint(
                self.user,
                self.title_e.get(),
                self.desc_e.get(),
            )
            self._show_info(f"Complaint submitted. ID: {complaint_id}")
            self.title_e.delete(0, tk.END)
            self.desc_e.delete(0, tk.END)
        except Exception as exc:
            self._show_error(exc)


class TenantRepairsTab(TenantBaseTab):
    title = "Repairs"

    def __init__(self, parent: tk.Widget, dashboard: TenantDashboardFrame) -> None:
        super().__init__(parent, dashboard)
        top = ttk.Frame(self, style="Surface.TFrame")
        top.pack(fill="x")

        req_box = ttk.LabelFrame(top, text="Submit Repair Request", padding=10)
        req_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        req_box.columnconfigure(1, weight=1)
        self.title_e = ttk.Entry(req_box, width=26)
        self.desc_e = ttk.Entry(req_box, width=44)
        self.priority_cb = ttk.Combobox(req_box, values=["LOW", "MEDIUM", "HIGH"], state="readonly", width=12)
        self.priority_cb.set("MEDIUM")

        ttk.Label(req_box, text="Title").grid(row=0, column=0, sticky="w")
        self.title_e.grid(row=0, column=1, sticky="ew")
        ttk.Label(req_box, text="Description").grid(row=1, column=0, sticky="w")
        self.desc_e.grid(row=1, column=1, sticky="ew")
        ttk.Label(req_box, text="Priority").grid(row=2, column=0, sticky="w")
        self.priority_cb.grid(row=2, column=1, sticky="w")
        ttk.Button(req_box, text="Submit Repair Request", command=self._submit).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        list_box = ttk.LabelFrame(self, text="Repair Progress", padding=10)
        list_box.pack(fill="both", expand=True, pady=(8, 0))
        cols = ("id", "property", "title", "priority", "status", "scheduled", "resolved")
        self.tree = create_treeview(list_box, cols, [
            ("id", "ID", 70),
            ("property", "Property", 120),
            ("title", "Title", 260),
            ("priority", "Priority", 100),
            ("status", "Status", 120),
            ("scheduled", "Scheduled", 120),
            ("resolved", "Resolved", 120),
        ])

    def _submit(self) -> None:
        try:
            req_id = self.service.tenant_request_repair(
                self.user,
                title=self.title_e.get(),
                description=self.desc_e.get(),
                priority=self.priority_cb.get(),
            )
            self._show_info(f"Repair request submitted. ID: {req_id}")
            self.title_e.delete(0, tk.END)
            self.desc_e.delete(0, tk.END)
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = self.service.tenant_repair_progress(self.user)
        for row in rows:
            insert_tree_row(
                self.tree,
                (
                    row["id"],
                    row["apartment_code"],
                    row["title"],
                    row["priority"],
                    row["status"],
                    row["scheduled_at"] or "",
                    row["resolved_at"] or "",
                ),
                status=str(row["status"]),
            )


class TenantChartsTab(TenantBaseTab):
    title = "Charts"

    def __init__(self, parent: tk.Widget, dashboard: TenantDashboardFrame) -> None:
        super().__init__(parent, dashboard)

        self.canvas1 = self._chart_canvas("Payment History by Month")
        self.canvas2 = self._chart_canvas("My Payments vs Close Neighbour Average")
        self.canvas3 = self._chart_canvas("My Late Payments per Property")

    def _chart_canvas(self, title: str) -> tk.Canvas:
        frame = ttk.LabelFrame(self, text=title, padding=8)
        frame.pack(fill="x", pady=(0, 8))
        canvas = tk.Canvas(frame, width=900, height=190, bg=COLORS["panel"], highlightthickness=0)
        canvas.pack(fill="x")
        return canvas

    def _draw_bar_chart(
        self,
        canvas: tk.Canvas,
        data: list[dict[str, Any]],
        label_key: str,
        value_key: str,
        palette: list[str],
    ) -> None:
        canvas.delete("all")
        w = int(canvas.winfo_width() or 900)
        h = int(canvas.winfo_height() or 190)
        if not data:
            canvas.create_text(w // 2, h // 2, text="No data", fill=COLORS["muted"], font=("SF Pro Text", 11))
            return

        max_val = max(float(item[value_key]) for item in data) or 1.0
        left_pad = 50
        right_pad = 20
        top_pad = 20
        bottom_pad = 40
        chart_w = w - left_pad - right_pad
        chart_h = h - top_pad - bottom_pad
        bar_gap = 8
        bar_w = max(18, (chart_w - bar_gap * (len(data) - 1)) // len(data))

        for marker in range(5):
            y = top_pad + (chart_h * marker / 4)
            value = max_val - (max_val * marker / 4)
            canvas.create_line(left_pad, y, left_pad + chart_w, y, fill="#20304a", dash=(2, 4))
            canvas.create_text(left_pad - 8, y, text=f"{value:.0f}", fill=COLORS["muted"], anchor="e", font=("SF Pro Text", 8))

        canvas.create_line(left_pad, top_pad, left_pad, top_pad + chart_h, fill="#475569")
        canvas.create_line(left_pad, top_pad + chart_h, left_pad + chart_w, top_pad + chart_h, fill="#475569")

        x = left_pad
        for idx, item in enumerate(data):
            val = float(item[value_key])
            label = str(item[label_key])
            bar_h = int((val / max_val) * chart_h) if max_val > 0 else 0
            y0 = top_pad + chart_h - bar_h
            y1 = top_pad + chart_h
            color = palette[idx % len(palette)]
            canvas.create_rectangle(x, y0, x + bar_w, y1, fill=color, outline="")
            canvas.create_text(x + bar_w // 2, y0 - 8, text=f"{val:.0f}", fill=COLORS["text"], font=("SF Pro Text", 9))
            canvas.create_text(x + bar_w // 2, y1 + 14, text=label, fill=COLORS["muted"], font=("SF Pro Text", 9))
            x += bar_w + bar_gap

    def refresh(self) -> None:
        history = self.service.tenant_payment_history_graph(self.user)
        compare = self.service.tenant_vs_neighbours_graph(self.user)
        late = self.service.tenant_late_per_property_graph(self.user)
        self._draw_bar_chart(self.canvas1, history, "billing_month", "paid_amount", [COLORS["accent"], COLORS["accent_2"]])
        self._draw_bar_chart(self.canvas2, compare, "label", "value", [COLORS["accent_2"], COLORS["accent"], COLORS["warn"]])
        self._draw_bar_chart(self.canvas3, late, "property_code", "late_amount", [COLORS["danger"], COLORS["warn"]])


class MainFrame(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        service: PamsService,
        user: CurrentUser,
        logout_callback: Callable[[], None],
    ) -> None:
        super().__init__(parent, style="Surface.TFrame")
        self.service = service
        self.user = user
        self.logout_callback = logout_callback
        self.city_map: dict[str, int] = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_header()
        self._build_dashboard_cards()
        self._build_tabs()

    def _build_header(self) -> None:
        header = ttk.Frame(self, style="Surface.TFrame", padding=(20, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Paragon Apartment Management System",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")

        sub = f"Signed in: {self.user.full_name} ({self.user.role})"
        ttk.Label(header, text=sub, style="Subtitle.TLabel").grid(row=1, column=0, sticky="w")

        ttk.Button(header, text="Refresh", style="Secondary.TButton", command=self.refresh_all).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(header, text="Logout", style="Danger.TButton", command=self.logout_callback).grid(
            row=0, column=2
        )

    def _build_dashboard_cards(self) -> None:
        self.summary_row = ttk.Frame(self, style="Surface.TFrame", padding=(20, 0, 20, 10))
        self.summary_row.grid(row=1, column=0, sticky="ew")
        for i in range(6):
            self.summary_row.columnconfigure(i, weight=1)

        self.summary_labels: dict[str, ttk.Label] = {}
        keys = [
            ("apartments_total", "Apartments"),
            ("apartments_occupied", "Occupied"),
            ("apartments_available", "Available"),
            ("tenants_total", "Tenants"),
            ("late_invoices", "Late Invoices"),
            ("late_amount", "Late Amount (£)"),
        ]
        for col, (key, title) in enumerate(keys):
            card = ttk.Frame(self.summary_row, style="Card.TFrame", padding=10)
            card.grid(row=0, column=col, sticky="nsew", padx=4)
            ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
            lbl = ttk.Label(card, text="0", style="CardValue.TLabel")
            lbl.pack(anchor="w")
            self.summary_labels[key] = lbl

        self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        try:
            data = self.service.dashboard_summary(self.user)
        except Exception as exc:
            messagebox.showerror("Dashboard", str(exc))
            return

        for key, lbl in self.summary_labels.items():
            value = data.get(key, 0)
            if key == "late_amount":
                lbl.configure(text=f"{float(value):.2f}")
            else:
                lbl.configure(text=str(value))

    def _build_tabs(self) -> None:
        panel = ttk.Frame(self, style="Surface.TFrame", padding=(20, 0, 20, 20))
        panel.grid(row=2, column=0, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(panel)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.tabs: list[BaseTab] = []

        if can(self.user.role, "tenant:view") or can(self.user.role, "tenant:create"):
            self.tabs.append(TenantTab(self.notebook, self))
        if can(self.user.role, "apartment:view") or can(self.user.role, "apartment:create"):
            self.tabs.append(ApartmentTab(self.notebook, self))
        if can(self.user.role, "maintenance:view"):
            self.tabs.append(MaintenanceTab(self.notebook, self))
        if can(self.user.role, "invoice:view"):
            self.tabs.append(BillingTab(self.notebook, self))
        if any(
            can(self.user.role, permission)
            for permission in ["report:occupancy", "report:financial", "report:maintenance"]
        ):
            self.tabs.append(ReportsTab(self.notebook, self))
        if can(self.user.role, "user:view") or can(self.user.role, "user:create"):
            self.tabs.append(UserAdminTab(self.notebook, self))

        for tab in self.tabs:
            self.notebook.add(tab, text=tab.title)

    def city_options(self) -> list[str]:
        rows = self.service.list_cities()
        self.city_map = {f"{r['id']} - {r['name']}": int(r["id"]) for r in rows if r["is_active"]}
        return list(self.city_map.keys())

    def resolve_city_id(self, value: str | None) -> int | None:
        if not value:
            return None
        if value in self.city_map:
            return self.city_map[value]
        try:
            return int(value)
        except ValueError:
            return None

    def refresh_all(self) -> None:
        self._refresh_dashboard()
        for tab in self.tabs:
            tab.refresh()


class BaseTab(ttk.Frame):
    title = "Base"

    def __init__(self, parent: tk.Widget, main: MainFrame) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=12)
        self.main = main

    def refresh(self) -> None:
        pass

    def _safe_int(self, value: str, field: str) -> int:
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{field} must be an integer") from exc

    def _show_error(self, exc: Exception) -> None:
        messagebox.showerror(self.title, str(exc))

    def _show_info(self, msg: str) -> None:
        messagebox.showinfo(self.title, msg)


class TenantTab(BaseTab):
    title = "Tenants"

    def __init__(self, parent: tk.Widget, main: MainFrame) -> None:
        super().__init__(parent, main)

        top = ttk.Frame(self, style="Surface.TFrame")
        top.pack(fill="x")

        form = ttk.LabelFrame(top, text="Register Tenant", padding=10)
        form.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.city_cb = ttk.Combobox(form, width=24, state="readonly")
        self.ni_e = ttk.Entry(form, width=18)
        self.fn_e = ttk.Entry(form, width=14)
        self.ln_e = ttk.Entry(form, width=14)
        self.phone_e = ttk.Entry(form, width=14)
        self.email_e = ttk.Entry(form, width=22)
        self.occ_e = ttk.Entry(form, width=14)
        self.ref_e = ttk.Entry(form, width=16)
        self.req_type_e = ttk.Entry(form, width=14)
        self.apartment_id_e = ttk.Entry(form, width=10)
        self.start_e = ttk.Entry(form, width=12)
        self.end_e = ttk.Entry(form, width=12)
        self.deposit_e = ttk.Entry(form, width=10)
        self.rent_e = ttk.Entry(form, width=10)

        fields = [
            ("City", self.city_cb),
            ("NI Number", self.ni_e),
            ("First Name", self.fn_e),
            ("Last Name", self.ln_e),
            ("Phone", self.phone_e),
            ("Email", self.email_e),
            ("Occupation", self.occ_e),
            ("References", self.ref_e),
            ("Required Type", self.req_type_e),
            ("Apartment ID (opt)", self.apartment_id_e),
            ("Lease Start YYYY-MM-DD", self.start_e),
            ("Lease End YYYY-MM-DD", self.end_e),
            ("Deposit", self.deposit_e),
            ("Monthly Rent", self.rent_e),
        ]
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        for i, (label, widget) in enumerate(fields):
            r = i // 2
            c = (i % 2) * 2
            ttk.Label(form, text=label).grid(row=r, column=c, sticky="w", padx=(0, 6), pady=(2, 2))
            widget.grid(row=r, column=c + 1, sticky="ew", padx=(0, 12), pady=(2, 2))

        action_row = ttk.Frame(form, style="Surface.TFrame")
        action_row.grid(row=8, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Button(action_row, text="Register Tenant", command=self._register).pack(side="left", padx=(0, 8))
        ttk.Button(action_row, text="Refresh", style="Secondary.TButton", command=self.refresh).pack(side="left")

        ops = ttk.LabelFrame(top, text="Tenant Operations", padding=10)
        ops.pack(side="right", fill="both")

        self.complaint_tenant_id = ttk.Entry(ops, width=12)
        self.complaint_title = ttk.Entry(ops, width=20)
        self.complaint_desc = ttk.Entry(ops, width=22)
        self.early_leave_lease_id = ttk.Entry(ops, width=12)
        self.early_leave_date = ttk.Entry(ops, width=14)
        ops.columnconfigure(1, weight=1)

        ttk.Label(ops, text="Complaint Tenant ID").grid(row=0, column=0, sticky="w")
        self.complaint_tenant_id.grid(row=0, column=1, sticky="ew")
        ttk.Label(ops, text="Complaint Title").grid(row=1, column=0, sticky="w")
        self.complaint_title.grid(row=1, column=1, sticky="ew")
        ttk.Label(ops, text="Complaint Description").grid(row=2, column=0, sticky="w")
        self.complaint_desc.grid(row=2, column=1, sticky="ew")
        ttk.Button(ops, text="Log Complaint", command=self._log_complaint).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(4, 10)
        )

        ttk.Separator(ops, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Label(ops, text="Early Leave Lease ID").grid(row=5, column=0, sticky="w")
        self.early_leave_lease_id.grid(row=5, column=1, sticky="ew")
        ttk.Label(ops, text="Requested End Date").grid(row=6, column=0, sticky="w")
        self.early_leave_date.grid(row=6, column=1, sticky="ew")
        ttk.Button(ops, text="Request Early Leave", command=self._early_leave).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(4, 0)
        )

        list_frame = ttk.LabelFrame(self, text="Tenant List", padding=10)
        list_frame.pack(fill="both", expand=True, pady=(8, 0))

        cols = ("id", "city", "ni", "name", "phone", "email", "occupation", "active")
        self.tree = create_treeview(list_frame, cols, [
            ("id", "ID", 60),
            ("city", "City", 120),
            ("ni", "NI Number", 120),
            ("name", "Name", 180),
            ("phone", "Phone", 120),
            ("email", "Email", 200),
            ("occupation", "Occupation", 140),
            ("active", "Active", 80),
        ], height=12)

        self.refresh()

    def _register(self) -> None:
        try:
            city_id = self.main.resolve_city_id(self.city_cb.get())
            apartment_text = self.apartment_id_e.get().strip()
            apartment_id = int(apartment_text) if apartment_text else None
            tenant_id = self.main.service.register_tenant(
                self.main.user,
                city_id=city_id or 0,
                ni_number=self.ni_e.get(),
                first_name=self.fn_e.get(),
                last_name=self.ln_e.get(),
                phone=self.phone_e.get(),
                email=self.email_e.get(),
                occupation=self.occ_e.get(),
                references_text=self.ref_e.get(),
                required_apartment_type=self.req_type_e.get(),
                apartment_id=apartment_id,
                lease_start=self.start_e.get().strip() or None,
                lease_end=self.end_e.get().strip() or None,
                deposit_amount=self.deposit_e.get() or 0,
                monthly_rent=self.rent_e.get() or 0,
            )
            self._show_info(f"Tenant registered. ID: {tenant_id}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _log_complaint(self) -> None:
        try:
            tenant_id = self._safe_int(self.complaint_tenant_id.get(), "Tenant ID")
            complaint_id = self.main.service.create_complaint(
                self.main.user,
                tenant_id,
                self.complaint_title.get(),
                self.complaint_desc.get(),
            )
            self._show_info(f"Complaint logged. ID: {complaint_id}")
        except Exception as exc:
            self._show_error(exc)

    def _early_leave(self) -> None:
        try:
            lease_id = self._safe_int(self.early_leave_lease_id.get(), "Lease ID")
            penalty = self.main.service.request_early_leave(
                self.main.user,
                lease_id,
                self.early_leave_date.get(),
            )
            self._show_info(f"Early leave request recorded. Penalty: £{penalty:.2f}")
        except Exception as exc:
            self._show_error(exc)

    def refresh(self) -> None:
        try:
            options = self.main.city_options()
            self.city_cb["values"] = options
            if options and not self.city_cb.get():
                self.city_cb.set(options[0])

            for item in self.tree.get_children():
                self.tree.delete(item)

            rows = self.main.service.list_tenants(self.main.user)
            for row in rows:
                insert_tree_row(
                    self.tree,
                    (
                        row["id"],
                        row["city_name"],
                        row["ni_number"],
                        row["full_name"],
                        row["phone"],
                        row["email"],
                        row["occupation"],
                        "Yes" if row["is_active"] else "No",
                    ),
                    status="ACTIVE" if row["is_active"] else "INACTIVE",
                )
        except Exception as exc:
            self._show_error(exc)


class ApartmentTab(BaseTab):
    title = "Apartments"

    def __init__(self, parent: tk.Widget, main: MainFrame) -> None:
        super().__init__(parent, main)

        form = ttk.LabelFrame(self, text="Apartment Registration", padding=10)
        form.pack(fill="x")

        self.city_cb = ttk.Combobox(form, width=25, state="readonly")
        self.code_e = ttk.Entry(form, width=14)
        self.address_e = ttk.Entry(form, width=34)
        self.type_e = ttk.Entry(form, width=18)
        self.rooms_e = ttk.Entry(form, width=8)
        self.rent_e = ttk.Entry(form, width=10)

        fields = [
            ("City", self.city_cb),
            ("Code", self.code_e),
            ("Address", self.address_e),
            ("Type", self.type_e),
            ("Rooms", self.rooms_e),
            ("Monthly Rent", self.rent_e),
        ]
        for column_index in [1, 3, 5, 7, 9, 11]:
            form.columnconfigure(column_index, weight=1)
        for i, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i * 2, sticky="w", padx=(0, 4))
            widget.grid(row=0, column=i * 2 + 1, sticky="ew", padx=(0, 10))

        ttk.Button(form, text="Add Apartment", command=self._add).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(form, text="Refresh", style="Secondary.TButton", command=self.refresh).grid(
            row=1, column=2, columnspan=2, sticky="ew", pady=(8, 0)
        )

        list_box = ttk.LabelFrame(self, text="Apartment List", padding=10)
        list_box.pack(fill="both", expand=True, pady=(8, 0))

        cols = ("id", "city", "code", "address", "type", "rooms", "rent", "status")
        self.tree = create_treeview(list_box, cols, [
            ("id", "ID", 50),
            ("city", "City", 110),
            ("code", "Code", 90),
            ("address", "Address", 260),
            ("type", "Type", 120),
            ("rooms", "Rooms", 80),
            ("rent", "Rent", 90),
            ("status", "Status", 100),
        ])

        self.refresh()

    def _add(self) -> None:
        try:
            city_id = self.main.resolve_city_id(self.city_cb.get())
            apartment_id = self.main.service.create_apartment(
                self.main.user,
                city_id=city_id or 0,
                code=self.code_e.get(),
                address=self.address_e.get(),
                apartment_type=self.type_e.get(),
                rooms=int(self.rooms_e.get()),
                monthly_rent=self.rent_e.get(),
            )
            self._show_info(f"Apartment created. ID: {apartment_id}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def refresh(self) -> None:
        try:
            options = self.main.city_options()
            self.city_cb["values"] = options
            if options and not self.city_cb.get():
                self.city_cb.set(options[0])

            for item in self.tree.get_children():
                self.tree.delete(item)

            rows = self.main.service.list_apartments(self.main.user)
            for row in rows:
                insert_tree_row(
                    self.tree,
                    (
                        row["id"],
                        row["city_name"],
                        row["code"],
                        row["address"],
                        row["apartment_type"],
                        row["rooms"],
                        f"£{float(row['monthly_rent']):.2f}",
                        row["status"],
                    ),
                    status=str(row["status"]),
                )
        except Exception as exc:
            self._show_error(exc)


class MaintenanceTab(BaseTab):
    title = "Maintenance"

    def __init__(self, parent: tk.Widget, main: MainFrame) -> None:
        super().__init__(parent, main)

        container = ttk.Frame(self, style="Surface.TFrame")
        container.pack(fill="x")

        req_box = ttk.LabelFrame(container, text="Create Request", padding=10)
        req_box.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.apartment_id_e = ttk.Entry(req_box, width=10)
        self.tenant_id_e = ttk.Entry(req_box, width=10)
        self.title_e = ttk.Entry(req_box, width=22)
        self.desc_e = ttk.Entry(req_box, width=30)
        self.priority_cb = ttk.Combobox(req_box, values=["LOW", "MEDIUM", "HIGH"], width=12, state="readonly")
        self.priority_cb.set("MEDIUM")
        req_box.columnconfigure(1, weight=1)

        for i, (label, widget) in enumerate(
            [
                ("Apartment ID", self.apartment_id_e),
                ("Tenant ID (opt)", self.tenant_id_e),
                ("Title", self.title_e),
                ("Description", self.desc_e),
                ("Priority", self.priority_cb),
            ]
        ):
            ttk.Label(req_box, text=label).grid(row=i, column=0, sticky="w")
            widget.grid(row=i, column=1, sticky="ew", pady=(0, 2))

        ttk.Button(req_box, text="Create", command=self._create_request).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        upd_box = ttk.LabelFrame(container, text="Update Request", padding=10)
        upd_box.pack(side="right", fill="both")

        self.req_id_e = ttk.Entry(upd_box, width=10)
        self.status_cb = ttk.Combobox(
            upd_box,
            values=["REPORTED", "SCHEDULED", "IN_PROGRESS", "RESOLVED"],
            width=14,
            state="readonly",
        )
        self.status_cb.set("SCHEDULED")
        self.scheduled_e = ttk.Entry(upd_box, width=14)
        self.notes_e = ttk.Entry(upd_box, width=24)
        self.hours_e = ttk.Entry(upd_box, width=10)
        self.cost_e = ttk.Entry(upd_box, width=10)
        upd_box.columnconfigure(1, weight=1)

        for i, (label, widget) in enumerate(
            [
                ("Request ID", self.req_id_e),
                ("Status", self.status_cb),
                ("Scheduled YYYY-MM-DD", self.scheduled_e),
                ("Resolution Notes", self.notes_e),
                ("Hours", self.hours_e),
                ("Cost", self.cost_e),
            ]
        ):
            ttk.Label(upd_box, text=label).grid(row=i, column=0, sticky="w")
            widget.grid(row=i, column=1, sticky="ew", pady=(0, 2))

        ttk.Button(upd_box, text="Apply Update", command=self._update_request).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        list_box = ttk.LabelFrame(self, text="Maintenance Requests", padding=10)
        list_box.pack(fill="both", expand=True, pady=(8, 0))

        cols = ("id", "city", "apartment", "title", "priority", "status", "scheduled", "resolved", "hours", "cost")
        self.tree = create_treeview(list_box, cols, [
            ("id", "ID", 50),
            ("city", "City", 100),
            ("apartment", "Apartment", 90),
            ("title", "Title", 200),
            ("priority", "Priority", 90),
            ("status", "Status", 120),
            ("scheduled", "Scheduled", 110),
            ("resolved", "Resolved", 110),
            ("hours", "Hours", 80),
            ("cost", "Cost", 80),
        ])

        self.refresh()

    def _create_request(self) -> None:
        try:
            apartment_id = self._safe_int(self.apartment_id_e.get(), "Apartment ID")
            tenant_txt = self.tenant_id_e.get().strip()
            tenant_id = int(tenant_txt) if tenant_txt else None
            req_id = self.main.service.create_maintenance_request(
                self.main.user,
                apartment_id=apartment_id,
                tenant_id=tenant_id,
                title=self.title_e.get(),
                description=self.desc_e.get(),
                priority=self.priority_cb.get(),
            )
            self._show_info(f"Maintenance request created: {req_id}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _update_request(self) -> None:
        try:
            request_id = self._safe_int(self.req_id_e.get(), "Request ID")
            self.main.service.update_maintenance(
                self.main.user,
                request_id=request_id,
                status=self.status_cb.get(),
                scheduled_at=self.scheduled_e.get().strip() or None,
                resolution_notes=self.notes_e.get(),
                time_spent_hours=self.hours_e.get() or 0,
                cost=self.cost_e.get() or 0,
            )
            self._show_info("Maintenance request updated")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def refresh(self) -> None:
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            rows = self.main.service.list_maintenance(self.main.user)
            for row in rows:
                insert_tree_row(
                    self.tree,
                    (
                        row["id"],
                        row["city_name"],
                        row["apartment_code"],
                        row["title"],
                        row["priority"],
                        row["status"],
                        row["scheduled_at"] or "",
                        row["resolved_at"] or "",
                        row["time_spent_hours"] or 0,
                        f"£{float(row['cost'] or 0):.2f}",
                    ),
                    status=str(row["status"]),
                )
        except Exception as exc:
            self._show_error(exc)


class BillingTab(BaseTab):
    title = "Billing"

    def __init__(self, parent: tk.Widget, main: MainFrame) -> None:
        super().__init__(parent, main)

        top = ttk.Frame(self, style="Surface.TFrame")
        top.pack(fill="x")

        inv_box = ttk.LabelFrame(top, text="Create Invoice", padding=10)
        inv_box.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.lease_id_e = ttk.Entry(inv_box, width=10)
        self.bill_month_e = ttk.Entry(inv_box, width=12)
        self.due_date_e = ttk.Entry(inv_box, width=12)
        self.amount_e = ttk.Entry(inv_box, width=10)
        inv_box.columnconfigure(1, weight=1)

        for i, (label, widget) in enumerate(
            [
                ("Lease ID", self.lease_id_e),
                ("Billing Month (YYYY-MM)", self.bill_month_e),
                ("Due Date YYYY-MM-DD", self.due_date_e),
                ("Amount", self.amount_e),
            ]
        ):
            ttk.Label(inv_box, text=label).grid(row=i, column=0, sticky="w")
            widget.grid(row=i, column=1, sticky="ew", pady=(0, 2))

        ttk.Button(inv_box, text="Create Invoice", command=self._create_invoice).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        pay_box = ttk.LabelFrame(top, text="Record Payment", padding=10)
        pay_box.pack(side="right", fill="both")

        self.inv_id_e = ttk.Entry(pay_box, width=10)
        self.pay_amount_e = ttk.Entry(pay_box, width=10)
        self.pay_date_e = ttk.Entry(pay_box, width=12)
        self.pay_method_e = ttk.Entry(pay_box, width=14)
        pay_box.columnconfigure(1, weight=1)

        for i, (label, widget) in enumerate(
            [
                ("Invoice ID", self.inv_id_e),
                ("Amount", self.pay_amount_e),
                ("Paid On YYYY-MM-DD", self.pay_date_e),
                ("Method", self.pay_method_e),
            ]
        ):
            ttk.Label(pay_box, text=label).grid(row=i, column=0, sticky="w")
            widget.grid(row=i, column=1, sticky="ew", pady=(0, 2))

        ttk.Button(pay_box, text="Record Payment", command=self._record_payment).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        ttk.Button(pay_box, text="Mark Late Invoices", style="Secondary.TButton", command=self._mark_late).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(4, 0)
        )

        list_box = ttk.LabelFrame(self, text="Invoices", padding=10)
        list_box.pack(fill="both", expand=True, pady=(8, 0))

        cols = ("id", "city", "tenant", "ni", "month", "due", "amount", "status")
        self.tree = create_treeview(list_box, cols, [
            ("id", "ID", 50),
            ("city", "City", 110),
            ("tenant", "Tenant", 180),
            ("ni", "NI", 110),
            ("month", "Billing Month", 120),
            ("due", "Due Date", 110),
            ("amount", "Amount", 90),
            ("status", "Status", 90),
        ])

        self.refresh()

    def _create_invoice(self) -> None:
        try:
            lease_id = self._safe_int(self.lease_id_e.get(), "Lease ID")
            inv_id = self.main.service.create_invoice(
                self.main.user,
                lease_id=lease_id,
                billing_month=self.bill_month_e.get(),
                due_date=self.due_date_e.get(),
                amount=self.amount_e.get(),
            )
            self._show_info(f"Invoice created: {inv_id}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _record_payment(self) -> None:
        try:
            invoice_id = self._safe_int(self.inv_id_e.get(), "Invoice ID")
            pay_id = self.main.service.record_payment(
                self.main.user,
                invoice_id=invoice_id,
                amount=self.pay_amount_e.get(),
                paid_on=self.pay_date_e.get(),
                method=self.pay_method_e.get(),
            )
            self._show_info(f"Payment recorded. ID: {pay_id}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _mark_late(self) -> None:
        try:
            count = self.main.service.mark_overdue_invoices()
            self._show_info(f"Late invoice update complete. Updated: {count}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def refresh(self) -> None:
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            rows = self.main.service.list_invoices(self.main.user)
            for row in rows:
                insert_tree_row(
                    self.tree,
                    (
                        row["id"],
                        row["city_name"],
                        row["tenant_name"],
                        row["ni_number"],
                        row["billing_month"],
                        row["due_date"],
                        f"£{float(row['amount']):.2f}",
                        row["status"],
                    ),
                    status=str(row["status"]),
                )
        except Exception as exc:
            self._show_error(exc)


class ReportsTab(BaseTab):
    title = "Reports"

    def __init__(self, parent: tk.Widget, main: MainFrame) -> None:
        super().__init__(parent, main)

        actions = ttk.Frame(self, style="Surface.TFrame")
        actions.pack(fill="x", pady=(0, 8))

        self.city_cb = ttk.Combobox(actions, width=30, state="readonly")
        self.city_cb.pack(side="left", padx=(0, 8))

        ttk.Button(actions, text="Occupancy", command=self._occupancy).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Financial", command=self._financial).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Maintenance", command=self._maintenance).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Clear", style="Secondary.TButton", command=self._clear).pack(side="left")

        self.output = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            bg="#0b1220",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            font=("SF Mono", 11),
            height=24,
        )
        self.output.pack(fill="both", expand=True)

        self.refresh()

    def _selected_city(self) -> int | None:
        return self.main.resolve_city_id(self.city_cb.get())

    def _write_table(self, title: str, rows: list[dict[str, Any]]) -> None:
        self.output.insert(tk.END, f"\n=== {title} ===\n")
        if not rows:
            self.output.insert(tk.END, "No records\n")
            return
        headers = list(rows[0].keys())
        self.output.insert(tk.END, " | ".join(headers) + "\n")
        self.output.insert(tk.END, "-" * 80 + "\n")
        for row in rows:
            self.output.insert(tk.END, " | ".join(str(row[h]) for h in headers) + "\n")

    def _occupancy(self) -> None:
        try:
            rows = self.main.service.report_occupancy(self.main.user, self._selected_city())
            self._write_table("Occupancy Report", rows)
        except Exception as exc:
            self._show_error(exc)

    def _financial(self) -> None:
        try:
            rows = self.main.service.report_financial(self.main.user, self._selected_city())
            self._write_table("Financial Summary", rows)
        except Exception as exc:
            self._show_error(exc)

    def _maintenance(self) -> None:
        try:
            rows = self.main.service.report_maintenance_cost(self.main.user, self._selected_city())
            self._write_table("Maintenance Cost Report", rows)
        except Exception as exc:
            self._show_error(exc)

    def _clear(self) -> None:
        self.output.delete("1.0", tk.END)

    def refresh(self) -> None:
        try:
            options = ["All Cities"] + self.main.city_options()
            self.city_cb["values"] = options
            if options and not self.city_cb.get():
                self.city_cb.set(options[0])
        except Exception as exc:
            self._show_error(exc)


class UserAdminTab(BaseTab):
    title = "Users & Cities"

    def __init__(self, parent: tk.Widget, main: MainFrame) -> None:
        super().__init__(parent, main)

        top = ttk.Frame(self, style="Surface.TFrame")
        top.pack(fill="x")

        user_box = ttk.LabelFrame(top, text="Create User", padding=10)
        user_box.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.username_e = ttk.Entry(user_box, width=16)
        self.full_name_e = ttk.Entry(user_box, width=18)
        self.role_cb = ttk.Combobox(
            user_box,
            values=[
                "FRONT_DESK",
                "FINANCE_MANAGER",
                "MAINTENANCE_STAFF",
                "ADMIN",
                "MANAGER",
                "TENANT",
            ],
            width=18,
            state="readonly",
        )
        self.role_cb.set("FRONT_DESK")
        self.city_cb = ttk.Combobox(user_box, width=24, state="readonly")
        self.tenant_id_e = ttk.Entry(user_box, width=16)
        self.password_e = ttk.Entry(user_box, width=16)
        user_box.columnconfigure(1, weight=1)

        for i, (label, widget) in enumerate(
            [
                ("Username", self.username_e),
                ("Full Name", self.full_name_e),
                ("Role", self.role_cb),
                ("City", self.city_cb),
                ("Tenant ID (for TENANT)", self.tenant_id_e),
                ("Password", self.password_e),
            ]
        ):
            ttk.Label(user_box, text=label).grid(row=i, column=0, sticky="w")
            widget.grid(row=i, column=1, sticky="ew", pady=(0, 2))

        ttk.Button(user_box, text="Create User", command=self._create_user).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        city_box = ttk.LabelFrame(top, text="Add New City", padding=10)
        city_box.pack(side="right", fill="both")
        self.city_name_e = ttk.Entry(city_box, width=18)
        city_box.columnconfigure(1, weight=1)
        ttk.Label(city_box, text="City Name").grid(row=0, column=0, sticky="w")
        self.city_name_e.grid(row=0, column=1, sticky="ew")
        ttk.Button(city_box, text="Add City", command=self._add_city).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        list_box = ttk.LabelFrame(self, text="System Users", padding=10)
        list_box.pack(fill="both", expand=True, pady=(8, 0))

        cols = ("id", "username", "name", "role", "city", "active")
        self.tree = create_treeview(list_box, cols, [
            ("id", "ID", 50),
            ("username", "Username", 160),
            ("name", "Name", 220),
            ("role", "Role", 170),
            ("city", "City", 160),
            ("active", "Active", 80),
        ])

        self.refresh()

    def _create_user(self) -> None:
        try:
            city_id = self.main.resolve_city_id(self.city_cb.get())
            tenant_txt = self.tenant_id_e.get().strip()
            tenant_id = int(tenant_txt) if tenant_txt else None
            user_id = self.main.service.create_user(
                self.main.user,
                username=self.username_e.get(),
                full_name=self.full_name_e.get(),
                role=self.role_cb.get(),
                city_id=city_id,
                password=self.password_e.get(),
                tenant_id=tenant_id,
            )
            self._show_info(f"User created: {user_id}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def _add_city(self) -> None:
        try:
            city_id = self.main.service.create_city(self.main.user, self.city_name_e.get())
            self._show_info(f"City added: {city_id}")
            self.refresh()
        except Exception as exc:
            self._show_error(exc)

    def refresh(self) -> None:
        try:
            options = self.main.city_options()
            self.city_cb["values"] = options
            if options and not self.city_cb.get():
                self.city_cb.set(options[0])

            for item in self.tree.get_children():
                self.tree.delete(item)

            rows = self.main.service.list_users(self.main.user)
            for row in rows:
                insert_tree_row(
                    self.tree,
                    (
                        row["id"],
                        row["username"],
                        row["full_name"],
                        row["role"],
                        row["city_name"] or "GLOBAL",
                        "Yes" if row["is_active"] else "No",
                    ),
                    status="ACTIVE" if row["is_active"] else "INACTIVE",
                )
        except Exception as exc:
            self._show_error(exc)
