"""Application service layer for PAMS."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.business_rules import calculate_early_leave_penalty, requires_notice_period
from app.config import AppConfig
from app.database import Database
from app.rbac import (
    ALL_ROLES,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_TENANT,
    AuthorizationError,
    CurrentUser,
    require_permission,
)
from app.security import hash_password, verify_password
from app.validators import (
    ValidationError,
    require_non_empty,
    validate_date_order,
    validate_email,
    validate_ni,
    validate_phone,
    validate_positive_money,
)


class PamsService:
    def __init__(self, db: Database, cfg: AppConfig) -> None:
        self.db = db
        self.cfg = cfg

    @staticmethod
    def _utcnow_naive() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def _parse_date(self, value: str) -> date:
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except Exception as exc:
            raise ValidationError("Date must be in YYYY-MM-DD format") from exc

    def _resolve_city_scope(self, user: CurrentUser, city_id: int | None) -> int | None:
        if user.role == ROLE_MANAGER:
            return city_id
        if user.role == ROLE_TENANT:
            if user.city_id is None:
                return city_id
            if city_id is not None and city_id != user.city_id:
                raise AuthorizationError("City scope violation")
            return user.city_id
        if user.city_id is None:
            raise AuthorizationError("User does not have city scope")
        if city_id is not None and city_id != user.city_id:
            raise AuthorizationError("City scope violation")
        return user.city_id

    def _require_tenant_identity(self, user: CurrentUser) -> int:
        if user.role != ROLE_TENANT or user.tenant_id is None:
            raise AuthorizationError("Tenant login is required")
        return user.tenant_id

    def _validate_card_details(self, card_number: str, expiry_mm_yy: str, cvv: str) -> None:
        digits = "".join(ch for ch in card_number if ch.isdigit())
        if len(digits) < 13 or len(digits) > 19:
            raise ValidationError("Card number length is invalid")
        if not self._luhn_valid(digits):
            raise ValidationError("Card number failed validation")

        exp = expiry_mm_yy.strip()
        if len(exp) != 5 or exp[2] != "/":
            raise ValidationError("Expiry must be MM/YY")
        try:
            month = int(exp[:2])
            year = int(exp[3:])
        except ValueError as exc:
            raise ValidationError("Expiry must be MM/YY") from exc
        if month < 1 or month > 12:
            raise ValidationError("Expiry month is invalid")

        now = self._utcnow_naive()
        current_yy = now.year % 100
        if year < current_yy or (year == current_yy and month < now.month):
            raise ValidationError("Card is expired")

        if not (cvv.isdigit() and len(cvv) in (3, 4)):
            raise ValidationError("CVV must be 3 or 4 digits")

    @staticmethod
    def _luhn_valid(number: str) -> bool:
        total = 0
        reverse_digits = number[::-1]
        for idx, ch in enumerate(reverse_digits):
            n = int(ch)
            if idx % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    def _log_action(
        self,
        actor: CurrentUser,
        action: str,
        entity: str,
        entity_id: int | None,
        details: str = "",
    ) -> None:
        self.db.execute(
            """
            INSERT INTO audit_logs (user_id, action, entity, entity_id, details)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (actor.id, action, entity, entity_id, details[:500]),
        )

    def list_cities(self) -> list[dict[str, Any]]:
        return self.db.execute(
            "SELECT id, name, is_active FROM cities ORDER BY name",
            fetchall=True,
        )

    def authenticate(self, username: str, plain_password: str) -> CurrentUser:
        username = require_non_empty(username, "Username")
        plain_password = require_non_empty(plain_password, "Password")

        row = self.db.execute(
            """
            SELECT id, username, full_name, role, city_id, password_hash, password_salt,
                   failed_login_attempts, locked_until, is_active, tenant_id
            FROM (
                SELECT u.id, u.username, u.full_name, u.role, u.city_id, u.password_hash, u.password_salt,
                       u.failed_login_attempts, u.locked_until, u.is_active, ta.tenant_id
                FROM users u
                LEFT JOIN tenant_accounts ta ON ta.user_id = u.id
            ) user_view
            WHERE username = %s
            """,
            (username,),
            fetchone=True,
        )
        if not row or not row["is_active"]:
            raise AuthorizationError("Invalid username or password")

        now = self._utcnow_naive()
        locked_until = row["locked_until"]
        if locked_until and locked_until > now:
            raise AuthorizationError(
                f"Account locked until {locked_until.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )

        if not verify_password(plain_password, row["password_hash"], row["password_salt"]):
            failed = int(row["failed_login_attempts"] or 0) + 1
            lock_until = None
            if failed >= self.cfg.max_failed_logins:
                lock_until = now + timedelta(minutes=self.cfg.lockout_minutes)
                failed = 0

            self.db.execute(
                """
                UPDATE users
                SET failed_login_attempts = %s,
                    locked_until = %s
                WHERE id = %s
                """,
                (failed, lock_until, row["id"]),
            )
            raise AuthorizationError("Invalid username or password")

        self.db.execute(
            """
            UPDATE users
            SET failed_login_attempts = 0,
                locked_until = NULL,
                last_login = UTC_TIMESTAMP()
            WHERE id = %s
            """,
            (row["id"],),
        )

        return CurrentUser(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            city_id=row["city_id"],
            tenant_id=row.get("tenant_id"),
        )

    def create_user(
        self,
        actor: CurrentUser,
        *,
        username: str,
        full_name: str,
        role: str,
        city_id: int | None,
        password: str,
        tenant_id: int | None = None,
    ) -> int:
        require_permission(actor, "user:create")
        username = require_non_empty(username, "Username").lower()
        full_name = require_non_empty(full_name, "Full name")
        role = require_non_empty(role, "Role")
        if role not in ALL_ROLES:
            raise ValidationError(f"Unknown role: {role}")

        if actor.role == ROLE_ADMIN:
            city_id = actor.city_id

        tenant_row: dict[str, Any] | None = None
        if role == ROLE_TENANT:
            if tenant_id is None:
                raise ValidationError("Tenant ID is required when creating a TENANT user")
            tenant_row = self.db.execute(
                "SELECT id, city_id FROM tenants WHERE id = %s",
                (tenant_id,),
                fetchone=True,
            )
            if not tenant_row:
                raise ValidationError("Tenant ID does not exist")
            if city_id is not None and city_id != tenant_row["city_id"]:
                raise ValidationError("Tenant belongs to a different city")
            if self.db.execute(
                "SELECT id FROM tenant_accounts WHERE tenant_id = %s",
                (tenant_id,),
                fetchone=True,
            ):
                raise ValidationError("Tenant already has a linked login account")
            city_id = int(tenant_row["city_id"])

        password_hash = hash_password(password)
        user_id = self.db.execute(
            """
            INSERT INTO users (username, full_name, role, city_id, password_hash, password_salt)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                full_name,
                role,
                city_id,
                password_hash.hash_b64,
                password_hash.salt_b64,
            ),
        )
        if role == ROLE_TENANT and tenant_id is not None:
            self.db.execute(
                "INSERT INTO tenant_accounts (user_id, tenant_id) VALUES (%s, %s)",
                (user_id, tenant_id),
            )
        self._log_action(actor, "CREATE", "users", int(user_id), f"username={username}")
        return int(user_id)

    def list_users(self, actor: CurrentUser) -> list[dict[str, Any]]:
        require_permission(actor, "user:view")
        if actor.role == ROLE_MANAGER:
            return self.db.execute(
                """
                SELECT u.id, u.username, u.full_name, u.role, c.name AS city_name, u.is_active
                FROM users u
                LEFT JOIN cities c ON c.id = u.city_id
                ORDER BY u.role, u.username
                """,
                fetchall=True,
            )

        return self.db.execute(
            """
            SELECT u.id, u.username, u.full_name, u.role, c.name AS city_name, u.is_active
            FROM users u
            LEFT JOIN cities c ON c.id = u.city_id
            WHERE u.city_id = %s
            ORDER BY u.role, u.username
            """,
            (actor.city_id,),
            fetchall=True,
        )

    def create_city(self, actor: CurrentUser, city_name: str) -> int:
        require_permission(actor, "city:create")
        city_name = require_non_empty(city_name, "City name")
        city_id = self.db.execute(
            "INSERT INTO cities (name) VALUES (%s)",
            (city_name,),
        )
        self._log_action(actor, "CREATE", "cities", int(city_id), city_name)
        return int(city_id)

    def create_apartment(
        self,
        actor: CurrentUser,
        *,
        city_id: int,
        code: str,
        address: str,
        apartment_type: str,
        rooms: int,
        monthly_rent: str | float,
    ) -> int:
        require_permission(actor, "apartment:create")
        city_id = self._resolve_city_scope(actor, int(city_id)) or int(city_id)
        code = require_non_empty(code, "Apartment code")
        address = require_non_empty(address, "Address")
        apartment_type = require_non_empty(apartment_type, "Apartment type")
        if int(rooms) <= 0:
            raise ValidationError("Rooms must be greater than zero")

        rent = validate_positive_money(monthly_rent, "Monthly rent")
        apartment_id = self.db.execute(
            """
            INSERT INTO apartments (city_id, code, address, apartment_type, rooms, monthly_rent, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'AVAILABLE')
            """,
            (city_id, code, address, apartment_type, int(rooms), rent),
        )
        self._log_action(actor, "CREATE", "apartments", int(apartment_id), code)
        return int(apartment_id)

    def list_apartments(
        self, actor: CurrentUser, city_id: int | None = None
    ) -> list[dict[str, Any]]:
        require_permission(actor, "apartment:view")
        city_id = self._resolve_city_scope(actor, city_id)

        if city_id is None:
            return self.db.execute(
                """
                SELECT a.id, c.name AS city_name, a.code, a.address, a.apartment_type,
                       a.rooms, a.monthly_rent, a.status
                FROM apartments a
                JOIN cities c ON c.id = a.city_id
                ORDER BY c.name, a.code
                """,
                fetchall=True,
            )

        return self.db.execute(
            """
            SELECT a.id, c.name AS city_name, a.code, a.address, a.apartment_type,
                   a.rooms, a.monthly_rent, a.status
            FROM apartments a
            JOIN cities c ON c.id = a.city_id
            WHERE a.city_id = %s
            ORDER BY a.code
            """,
            (city_id,),
            fetchall=True,
        )

    def register_tenant(
        self,
        actor: CurrentUser,
        *,
        city_id: int,
        ni_number: str,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        occupation: str,
        references_text: str,
        required_apartment_type: str,
        apartment_id: int | None,
        lease_start: str | None,
        lease_end: str | None,
        deposit_amount: str | float,
        monthly_rent: str | float,
    ) -> int:
        require_permission(actor, "tenant:create")
        city_id = self._resolve_city_scope(actor, int(city_id)) or int(city_id)

        ni_number = validate_ni(ni_number)
        first_name = require_non_empty(first_name, "First name")
        last_name = require_non_empty(last_name, "Last name")
        phone = validate_phone(phone)
        email = validate_email(email)
        occupation = require_non_empty(occupation, "Occupation")
        required_apartment_type = require_non_empty(
            required_apartment_type, "Required apartment type"
        )

        deposit = validate_positive_money(deposit_amount, "Deposit amount")
        rent = validate_positive_money(monthly_rent, "Monthly rent")

        tenant_id = self.db.execute(
            """
            INSERT INTO tenants (
                city_id, ni_number, first_name, last_name, phone, email,
                occupation, references_text, required_apartment_type, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                city_id,
                ni_number,
                first_name,
                last_name,
                phone,
                email,
                occupation,
                references_text,
                required_apartment_type,
                actor.id,
            ),
        )

        if apartment_id and lease_start and lease_end:
            start_date = self._parse_date(lease_start)
            end_date = self._parse_date(lease_end)
            validate_date_order(start_date, end_date)

            apt = self.db.execute(
                "SELECT id, city_id, status FROM apartments WHERE id = %s",
                (apartment_id,),
                fetchone=True,
            )
            if not apt:
                raise ValidationError("Apartment does not exist")
            if apt["city_id"] != city_id:
                raise ValidationError("Apartment belongs to a different city")
            if apt["status"] != "AVAILABLE":
                raise ValidationError("Apartment is not available")

            self.db.execute(
                """
                INSERT INTO leases (
                    tenant_id, apartment_id, start_date, end_date,
                    monthly_rent, deposit_amount, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
                """,
                (tenant_id, apartment_id, start_date, end_date, rent, deposit),
            )
            self.db.execute(
                "UPDATE apartments SET status = 'OCCUPIED' WHERE id = %s",
                (apartment_id,),
            )

        self._log_action(actor, "CREATE", "tenants", int(tenant_id), ni_number)
        return int(tenant_id)

    def list_tenants(self, actor: CurrentUser, city_id: int | None = None) -> list[dict[str, Any]]:
        require_permission(actor, "tenant:view")
        city_id = self._resolve_city_scope(actor, city_id)

        if city_id is None:
            return self.db.execute(
                """
                SELECT t.id, c.name AS city_name, t.ni_number,
                       CONCAT(t.first_name, ' ', t.last_name) AS full_name,
                       t.phone, t.email, t.occupation, t.is_active
                FROM tenants t
                JOIN cities c ON c.id = t.city_id
                ORDER BY c.name, t.last_name, t.first_name
                """,
                fetchall=True,
            )

        return self.db.execute(
            """
            SELECT t.id, c.name AS city_name, t.ni_number,
                   CONCAT(t.first_name, ' ', t.last_name) AS full_name,
                   t.phone, t.email, t.occupation, t.is_active
            FROM tenants t
            JOIN cities c ON c.id = t.city_id
            WHERE t.city_id = %s
            ORDER BY t.last_name, t.first_name
            """,
            (city_id,),
            fetchall=True,
        )

    def list_leases(self, actor: CurrentUser, city_id: int | None = None) -> list[dict[str, Any]]:
        require_permission(actor, "lease:view")
        city_id = self._resolve_city_scope(actor, city_id)

        query = """
            SELECT l.id, c.name AS city_name, a.code AS apartment_code,
                   CONCAT(t.first_name, ' ', t.last_name) AS tenant_name,
                   l.start_date, l.end_date, l.monthly_rent, l.status
            FROM leases l
            JOIN tenants t ON t.id = l.tenant_id
            JOIN apartments a ON a.id = l.apartment_id
            JOIN cities c ON c.id = a.city_id
        """
        params: tuple[Any, ...] = ()
        if city_id is not None:
            query += " WHERE a.city_id = %s"
            params = (city_id,)
        query += " ORDER BY l.start_date DESC"
        return self.db.execute(query, params, fetchall=True)

    def request_early_leave(
        self,
        actor: CurrentUser,
        lease_id: int,
        requested_end_date: str,
    ) -> float:
        require_permission(actor, "lease:update")

        lease = self.db.execute(
            """
            SELECT l.id, l.monthly_rent, l.status, l.apartment_id, a.city_id
            FROM leases l
            JOIN apartments a ON a.id = l.apartment_id
            WHERE l.id = %s
            """,
            (lease_id,),
            fetchone=True,
        )
        if not lease:
            raise ValidationError("Lease not found")

        scope_city = self._resolve_city_scope(actor, lease["city_id"])
        if scope_city and scope_city != lease["city_id"]:
            raise AuthorizationError("City scope violation")

        req_date = self._parse_date(requested_end_date)
        if not requires_notice_period(date.today(), req_date, min_days=30):
            raise ValidationError("Tenant must provide at least 1 month notice")

        penalty = calculate_early_leave_penalty(float(lease["monthly_rent"]))

        self.db.execute(
            """
            UPDATE leases
            SET notice_given_date = %s,
                requested_end_date = %s,
                early_leave_penalty = %s,
                status = 'EARLY_LEAVE_REQUESTED',
                updated_at = UTC_TIMESTAMP()
            WHERE id = %s
            """,
            (date.today(), req_date, penalty, lease_id),
        )

        self._log_action(
            actor,
            "UPDATE",
            "leases",
            lease_id,
            f"Early leave requested; penalty={penalty}",
        )
        return penalty

    def deactivate_tenant(self, actor: CurrentUser, tenant_id: int) -> None:
        require_permission(actor, "tenant:delete")
        tenant = self.db.execute(
            "SELECT id, city_id FROM tenants WHERE id = %s",
            (tenant_id,),
            fetchone=True,
        )
        if not tenant:
            raise ValidationError("Tenant not found")
        self._resolve_city_scope(actor, tenant["city_id"])
        self.db.execute(
            "UPDATE tenants SET is_active = 0 WHERE id = %s",
            (tenant_id,),
        )
        self._log_action(actor, "UPDATE", "tenants", tenant_id, "deactivated")

    def create_complaint(
        self,
        actor: CurrentUser,
        tenant_id: int,
        title: str,
        description: str,
    ) -> int:
        require_permission(actor, "complaint:create")
        title = require_non_empty(title, "Complaint title")
        description = require_non_empty(description, "Complaint description")

        tenant = self.db.execute(
            "SELECT id, city_id FROM tenants WHERE id = %s",
            (tenant_id,),
            fetchone=True,
        )
        if not tenant:
            raise ValidationError("Tenant not found")
        self._resolve_city_scope(actor, tenant["city_id"])

        complaint_id = self.db.execute(
            """
            INSERT INTO complaints (tenant_id, title, description, status, created_by)
            VALUES (%s, %s, %s, 'OPEN', %s)
            """,
            (tenant_id, title, description, actor.id),
        )
        self._log_action(actor, "CREATE", "complaints", int(complaint_id), title)
        return int(complaint_id)

    def create_maintenance_request(
        self,
        actor: CurrentUser,
        *,
        apartment_id: int,
        tenant_id: int | None,
        title: str,
        description: str,
        priority: str,
    ) -> int:
        require_permission(actor, "maintenance:create")
        title = require_non_empty(title, "Maintenance title")
        description = require_non_empty(description, "Maintenance description")
        priority = require_non_empty(priority, "Priority").upper()

        apartment = self.db.execute(
            "SELECT id, city_id FROM apartments WHERE id = %s",
            (apartment_id,),
            fetchone=True,
        )
        if not apartment:
            raise ValidationError("Apartment not found")

        self._resolve_city_scope(actor, apartment["city_id"])

        req_id = self.db.execute(
            """
            INSERT INTO maintenance_requests (
                apartment_id, tenant_id, title, description, priority, status, requested_by
            )
            VALUES (%s, %s, %s, %s, %s, 'REPORTED', %s)
            """,
            (apartment_id, tenant_id, title, description, priority, actor.id),
        )
        self._log_action(actor, "CREATE", "maintenance_requests", int(req_id), title)
        return int(req_id)

    def list_maintenance(
        self,
        actor: CurrentUser,
        status: str | None = None,
        city_id: int | None = None,
    ) -> list[dict[str, Any]]:
        require_permission(actor, "maintenance:view")
        city_id = self._resolve_city_scope(actor, city_id)

        where: list[str] = []
        params: list[Any] = []
        if status:
            where.append("m.status = %s")
            params.append(status)
        if city_id is not None:
            where.append("a.city_id = %s")
            params.append(city_id)

        where_sql = ""
        if where:
            where_sql = "WHERE " + " AND ".join(where)

        return self.db.execute(
            f"""
            SELECT m.id, c.name AS city_name, a.code AS apartment_code,
                   m.title, m.priority, m.status, m.scheduled_at,
                   m.resolved_at, m.time_spent_hours, m.cost
            FROM maintenance_requests m
            JOIN apartments a ON a.id = m.apartment_id
            JOIN cities c ON c.id = a.city_id
            {where_sql}
            ORDER BY m.created_at DESC
            """,
            tuple(params),
            fetchall=True,
        )

    def update_maintenance(
        self,
        actor: CurrentUser,
        *,
        request_id: int,
        status: str,
        scheduled_at: str | None,
        resolution_notes: str,
        time_spent_hours: str | float,
        cost: str | float,
    ) -> None:
        require_permission(actor, "maintenance:update")
        status = require_non_empty(status, "Status").upper()

        row = self.db.execute(
            """
            SELECT m.id, a.city_id
            FROM maintenance_requests m
            JOIN apartments a ON a.id = m.apartment_id
            WHERE m.id = %s
            """,
            (request_id,),
            fetchone=True,
        )
        if not row:
            raise ValidationError("Maintenance request not found")

        self._resolve_city_scope(actor, row["city_id"])

        scheduled_date = self._parse_date(scheduled_at) if scheduled_at else None
        spent = validate_positive_money(time_spent_hours or 0, "Time spent hours")
        cost_amount = validate_positive_money(cost or 0, "Maintenance cost")

        resolved_at = date.today() if status == "RESOLVED" else None
        self.db.execute(
            """
            UPDATE maintenance_requests
            SET status = %s,
                scheduled_at = %s,
                resolved_at = %s,
                resolved_by = %s,
                resolution_notes = %s,
                time_spent_hours = %s,
                cost = %s,
                updated_at = UTC_TIMESTAMP()
            WHERE id = %s
            """,
            (
                status,
                scheduled_date,
                resolved_at,
                actor.id,
                resolution_notes,
                spent,
                cost_amount,
                request_id,
            ),
        )
        self._log_action(actor, "UPDATE", "maintenance_requests", request_id, status)

    def create_invoice(
        self,
        actor: CurrentUser,
        *,
        lease_id: int,
        billing_month: str,
        due_date: str,
        amount: str | float,
    ) -> int:
        require_permission(actor, "invoice:create")
        due = self._parse_date(due_date)
        bill_month = require_non_empty(billing_month, "Billing month")
        bill_amount = validate_positive_money(amount, "Invoice amount")

        lease = self.db.execute(
            """
            SELECT l.id, a.city_id
            FROM leases l
            JOIN apartments a ON a.id = l.apartment_id
            WHERE l.id = %s
            """,
            (lease_id,),
            fetchone=True,
        )
        if not lease:
            raise ValidationError("Lease not found")
        self._resolve_city_scope(actor, lease["city_id"])

        invoice_id = self.db.execute(
            """
            INSERT INTO invoices (lease_id, billing_month, due_date, amount, status, created_by)
            VALUES (%s, %s, %s, %s, 'PENDING', %s)
            """,
            (lease_id, bill_month, due, bill_amount, actor.id),
        )
        self._log_action(actor, "CREATE", "invoices", int(invoice_id), bill_month)
        return int(invoice_id)

    def list_invoices(
        self,
        actor: CurrentUser,
        status: str | None = None,
        city_id: int | None = None,
    ) -> list[dict[str, Any]]:
        require_permission(actor, "invoice:view")
        city_id = self._resolve_city_scope(actor, city_id)

        where: list[str] = []
        params: list[Any] = []
        if status:
            where.append("i.status = %s")
            params.append(status)
        if city_id is not None:
            where.append("a.city_id = %s")
            params.append(city_id)

        where_sql = ""
        if where:
            where_sql = "WHERE " + " AND ".join(where)

        return self.db.execute(
            f"""
            SELECT i.id, i.billing_month, i.due_date, i.amount, i.status,
                   t.ni_number, CONCAT(t.first_name, ' ', t.last_name) AS tenant_name,
                   c.name AS city_name
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            JOIN tenants t ON t.id = l.tenant_id
            JOIN apartments a ON a.id = l.apartment_id
            JOIN cities c ON c.id = a.city_id
            {where_sql}
            ORDER BY i.due_date DESC, i.id DESC
            """,
            tuple(params),
            fetchall=True,
        )

    def record_payment(
        self,
        actor: CurrentUser,
        *,
        invoice_id: int,
        amount: str | float,
        paid_on: str,
        method: str,
    ) -> int:
        require_permission(actor, "payment:record")
        paid_date = self._parse_date(paid_on)
        amount_paid = validate_positive_money(amount, "Paid amount")
        method = require_non_empty(method, "Payment method")

        invoice = self.db.execute(
            """
            SELECT i.id, i.amount, i.status, a.city_id, COALESCE(SUM(p.amount), 0) AS paid_total
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            JOIN apartments a ON a.id = l.apartment_id
            LEFT JOIN payments p ON p.invoice_id = i.id
            WHERE i.id = %s
            GROUP BY i.id, i.amount, i.status, a.city_id
            """,
            (invoice_id,),
            fetchone=True,
        )
        if not invoice:
            raise ValidationError("Invoice not found")

        self._resolve_city_scope(actor, invoice["city_id"])

        outstanding = round(float(invoice["amount"]) - float(invoice["paid_total"]), 2)
        if outstanding <= 0:
            raise ValidationError("Invoice is already fully paid")
        if amount_paid > outstanding:
            raise ValidationError(f"Paid amount cannot exceed outstanding balance ({outstanding:.2f})")

        receipt_no = f"RCT-{invoice_id}-{int(self._utcnow_naive().timestamp())}"

        payment_id = self.db.execute(
            """
            INSERT INTO payments (invoice_id, amount, paid_on, method, recorded_by, receipt_no)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (invoice_id, amount_paid, paid_date, method, actor.id, receipt_no),
        )

        remaining = round(outstanding - amount_paid, 2)
        new_status = "PAID" if remaining <= 0 else "PARTIAL"
        paid_at = paid_date if new_status == "PAID" else None
        self.db.execute(
            "UPDATE invoices SET status = %s, paid_at = %s WHERE id = %s",
            (new_status, paid_at, invoice_id),
        )

        self._log_action(actor, "CREATE", "payments", int(payment_id), receipt_no)
        return int(payment_id)

    def mark_overdue_invoices(self) -> int:
        return int(
            self.db.execute(
                """
                UPDATE invoices
                SET status = 'LATE'
                WHERE status IN ('PENDING', 'PARTIAL')
                  AND due_date < CURDATE()
                """,
            )
            or 0
        )

    def tenant_profile(self, actor: CurrentUser) -> dict[str, Any]:
        require_permission(actor, "tenant_portal:view")
        tenant_id = self._require_tenant_identity(actor)
        return self.db.execute(
            """
            SELECT t.id AS tenant_id, t.city_id, c.name AS city_name,
                   CONCAT(t.first_name, ' ', t.last_name) AS tenant_name,
                   t.email, t.phone, l.id AS lease_id, a.id AS apartment_id,
                   a.code AS apartment_code, a.address, a.apartment_type,
                   l.monthly_rent
            FROM tenants t
            JOIN cities c ON c.id = t.city_id
            LEFT JOIN leases l ON l.tenant_id = t.id AND l.status IN ('ACTIVE', 'EARLY_LEAVE_REQUESTED')
            LEFT JOIN apartments a ON a.id = l.apartment_id
            WHERE t.id = %s
            ORDER BY l.start_date DESC
            LIMIT 1
            """,
            (tenant_id,),
            fetchone=True,
        )

    def tenant_payment_records(self, actor: CurrentUser) -> list[dict[str, Any]]:
        require_permission(actor, "tenant:own_payments:view")
        tenant_id = self._require_tenant_identity(actor)
        return self.db.execute(
            """
            SELECT i.id AS invoice_id, i.billing_month, i.due_date, i.amount,
                   i.status, i.paid_at, a.code AS apartment_code,
                   COALESCE(SUM(p.amount), 0) AS paid_total,
                   ROUND(i.amount - COALESCE(SUM(p.amount), 0), 2) AS outstanding
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            JOIN apartments a ON a.id = l.apartment_id
            LEFT JOIN payments p ON p.invoice_id = i.id
            WHERE l.tenant_id = %s
            GROUP BY i.id, i.billing_month, i.due_date, i.amount, i.status, i.paid_at, a.code
            ORDER BY i.due_date DESC, i.id DESC
            """,
            (tenant_id,),
            fetchall=True,
        )

    def tenant_late_alerts(self, actor: CurrentUser) -> list[dict[str, Any]]:
        require_permission(actor, "tenant:own_late_alerts:view")
        tenant_id = self._require_tenant_identity(actor)
        return self.db.execute(
            """
            SELECT i.id AS invoice_id, i.billing_month, i.due_date, i.amount, i.status,
                   a.code AS apartment_code
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            JOIN apartments a ON a.id = l.apartment_id
            WHERE l.tenant_id = %s
              AND i.status = 'LATE'
            ORDER BY i.due_date DESC
            """,
            (tenant_id,),
            fetchall=True,
        )

    def tenant_submit_complaint(self, actor: CurrentUser, title: str, description: str) -> int:
        require_permission(actor, "tenant:own_complaint:create")
        tenant_id = self._require_tenant_identity(actor)
        title = require_non_empty(title, "Complaint title")
        description = require_non_empty(description, "Complaint description")
        complaint_id = self.db.execute(
            """
            INSERT INTO complaints (tenant_id, title, description, status, created_by)
            VALUES (%s, %s, %s, 'OPEN', %s)
            """,
            (tenant_id, title, description, actor.id),
        )
        self._log_action(actor, "CREATE", "complaints", int(complaint_id), title)
        return int(complaint_id)

    def tenant_request_repair(
        self,
        actor: CurrentUser,
        *,
        title: str,
        description: str,
        priority: str,
    ) -> int:
        require_permission(actor, "tenant:own_repair:create")
        tenant_profile = self.tenant_profile(actor)
        apartment_id = tenant_profile.get("apartment_id")
        if not apartment_id:
            raise ValidationError("No active apartment assignment found for tenant")
        tenant_id = self._require_tenant_identity(actor)
        title = require_non_empty(title, "Maintenance title")
        description = require_non_empty(description, "Maintenance description")
        priority = require_non_empty(priority, "Priority").upper()
        if priority not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValidationError("Priority must be LOW, MEDIUM or HIGH")

        req_id = self.db.execute(
            """
            INSERT INTO maintenance_requests (
                apartment_id, tenant_id, title, description, priority, status, requested_by
            )
            VALUES (%s, %s, %s, %s, %s, 'REPORTED', %s)
            """,
            (int(apartment_id), tenant_id, title, description, priority, actor.id),
        )
        self._log_action(actor, "CREATE", "maintenance_requests", int(req_id), title)
        return int(req_id)

    def tenant_repair_progress(self, actor: CurrentUser) -> list[dict[str, Any]]:
        require_permission(actor, "tenant:own_repair:view")
        tenant_id = self._require_tenant_identity(actor)
        return self.db.execute(
            """
            SELECT m.id, a.code AS apartment_code, m.title, m.priority, m.status,
                   m.scheduled_at, m.resolved_at, m.resolution_notes
            FROM maintenance_requests m
            JOIN apartments a ON a.id = m.apartment_id
            WHERE m.tenant_id = %s
            ORDER BY m.created_at DESC
            """,
            (tenant_id,),
            fetchall=True,
        )

    def tenant_payment_history_graph(self, actor: CurrentUser) -> list[dict[str, Any]]:
        require_permission(actor, "tenant:own_graph:view")
        tenant_id = self._require_tenant_identity(actor)
        return self.db.execute(
            """
            SELECT i.billing_month,
                   ROUND(COALESCE(SUM(p.amount), 0), 2) AS paid_amount
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            LEFT JOIN payments p ON p.invoice_id = i.id
            WHERE l.tenant_id = %s
            GROUP BY i.billing_month
            ORDER BY i.billing_month
            """,
            (tenant_id,),
            fetchall=True,
        )

    def tenant_vs_neighbours_graph(self, actor: CurrentUser) -> list[dict[str, Any]]:
        require_permission(actor, "tenant:own_graph:view")
        tenant_id = self._require_tenant_identity(actor)
        tenant_row = self.db.execute(
            """
            SELECT t.id, t.city_id
            FROM tenants t
            WHERE t.id = %s
            """,
            (tenant_id,),
            fetchone=True,
        )
        if not tenant_row:
            return []

        own_paid = self.db.execute(
            """
            SELECT ROUND(COALESCE(SUM(p.amount), 0), 2) AS amount
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            JOIN leases l ON l.id = i.lease_id
            WHERE l.tenant_id = %s
            """,
            (tenant_id,),
            fetchone=True,
        )["amount"]

        neighbour_paid = self.db.execute(
            """
            SELECT ROUND(COALESCE(AVG(tenant_total), 0), 2) AS avg_amount
            FROM (
                SELECT l.tenant_id, COALESCE(SUM(p.amount), 0) AS tenant_total
                FROM leases l
                JOIN tenants t ON t.id = l.tenant_id
                LEFT JOIN invoices i ON i.lease_id = l.id
                LEFT JOIN payments p ON p.invoice_id = i.id
                WHERE t.city_id = %s
                  AND t.id <> %s
                GROUP BY l.tenant_id
            ) x
            """,
            (tenant_row["city_id"], tenant_id),
            fetchone=True,
        )["avg_amount"]

        return [
            {"label": "My Payments", "value": float(own_paid or 0)},
            {"label": "Neighbour Avg", "value": float(neighbour_paid or 0)},
        ]

    def tenant_late_per_property_graph(self, actor: CurrentUser) -> list[dict[str, Any]]:
        require_permission(actor, "tenant:own_graph:view")
        tenant_id = self._require_tenant_identity(actor)
        return self.db.execute(
            """
            SELECT a.code AS property_code,
                   ROUND(COALESCE(SUM(CASE WHEN i.status = 'LATE' THEN i.amount ELSE 0 END), 0), 2) AS late_amount
            FROM leases l
            JOIN apartments a ON a.id = l.apartment_id
            LEFT JOIN invoices i ON i.lease_id = l.id
            WHERE l.tenant_id = %s
            GROUP BY a.code
            ORDER BY a.code
            """,
            (tenant_id,),
            fetchall=True,
        )

    def tenant_make_card_payment(
        self,
        actor: CurrentUser,
        *,
        invoice_id: int,
        amount: str | float,
        paid_on: str,
        card_number: str,
        expiry_mm_yy: str,
        cvv: str,
    ) -> int:
        require_permission(actor, "tenant:own_payment:record")
        tenant_id = self._require_tenant_identity(actor)
        self._validate_card_details(card_number, expiry_mm_yy, cvv)

        invoice = self.db.execute(
            """
            SELECT i.id, i.amount, i.status, COALESCE(SUM(p.amount), 0) AS paid_total
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            LEFT JOIN payments p ON p.invoice_id = i.id
            WHERE i.id = %s
              AND l.tenant_id = %s
            GROUP BY i.id, i.amount, i.status
            """,
            (invoice_id, tenant_id),
            fetchone=True,
        )
        if not invoice:
            raise ValidationError("Invoice not found for tenant")

        outstanding = round(float(invoice["amount"]) - float(invoice["paid_total"]), 2)
        if outstanding <= 0:
            raise ValidationError("Invoice is already fully paid")

        amount_paid = validate_positive_money(amount, "Payment amount")
        if amount_paid > outstanding:
            raise ValidationError(f"Amount exceeds outstanding balance ({outstanding:.2f})")

        paid_date = self._parse_date(paid_on)
        receipt_no = f"TEN-{invoice_id}-{int(self._utcnow_naive().timestamp())}"
        payment_id = self.db.execute(
            """
            INSERT INTO payments (invoice_id, amount, paid_on, method, recorded_by, receipt_no)
            VALUES (%s, %s, %s, 'CARD', %s, %s)
            """,
            (invoice_id, amount_paid, paid_date, actor.id, receipt_no),
        )

        remaining = round(outstanding - amount_paid, 2)
        new_status = "PAID" if remaining <= 0 else "PARTIAL"
        paid_at = paid_date if new_status == "PAID" else None
        self.db.execute(
            "UPDATE invoices SET status = %s, paid_at = %s WHERE id = %s",
            (new_status, paid_at, invoice_id),
        )
        self._log_action(actor, "CREATE", "payments", int(payment_id), f"{receipt_no}|CARD")
        return int(payment_id)

    def report_occupancy(
        self, actor: CurrentUser, city_id: int | None = None
    ) -> list[dict[str, Any]]:
        require_permission(actor, "report:occupancy")
        city_id = self._resolve_city_scope(actor, city_id)

        query = """
            SELECT c.name AS city_name,
                   COUNT(*) AS total_apartments,
                   SUM(CASE WHEN a.status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied,
                   SUM(CASE WHEN a.status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available,
                   ROUND((SUM(CASE WHEN a.status = 'OCCUPIED' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS occupancy_percent
            FROM apartments a
            JOIN cities c ON c.id = a.city_id
        """
        params: tuple[Any, ...] = ()
        if city_id is not None:
            query += " WHERE a.city_id = %s"
            params = (city_id,)
        query += " GROUP BY c.name ORDER BY c.name"

        return self.db.execute(query, params, fetchall=True)

    def report_financial(
        self, actor: CurrentUser, city_id: int | None = None
    ) -> list[dict[str, Any]]:
        require_permission(actor, "report:financial")
        city_id = self._resolve_city_scope(actor, city_id)

        query = """
            SELECT c.name AS city_name,
                   SUM(CASE WHEN i.status = 'PAID' THEN i.amount ELSE 0 END) AS collected_rent,
                   SUM(CASE WHEN i.status IN ('PENDING', 'PARTIAL', 'LATE') THEN i.amount ELSE 0 END) AS pending_rent,
                   SUM(CASE WHEN i.status = 'LATE' THEN i.amount ELSE 0 END) AS late_rent
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            JOIN apartments a ON a.id = l.apartment_id
            JOIN cities c ON c.id = a.city_id
        """
        params: tuple[Any, ...] = ()
        if city_id is not None:
            query += " WHERE a.city_id = %s"
            params = (city_id,)
        query += " GROUP BY c.name ORDER BY c.name"

        return self.db.execute(query, params, fetchall=True)

    def report_maintenance_cost(
        self, actor: CurrentUser, city_id: int | None = None
    ) -> list[dict[str, Any]]:
        require_permission(actor, "report:maintenance")
        city_id = self._resolve_city_scope(actor, city_id)

        query = """
            SELECT c.name AS city_name,
                   COUNT(m.id) AS total_requests,
                   SUM(CASE WHEN m.status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_requests,
                   ROUND(COALESCE(SUM(m.cost), 0), 2) AS total_cost,
                   ROUND(COALESCE(AVG(NULLIF(m.time_spent_hours, 0)), 0), 2) AS avg_hours
            FROM maintenance_requests m
            JOIN apartments a ON a.id = m.apartment_id
            JOIN cities c ON c.id = a.city_id
        """
        params: tuple[Any, ...] = ()
        if city_id is not None:
            query += " WHERE a.city_id = %s"
            params = (city_id,)
        query += " GROUP BY c.name ORDER BY c.name"

        return self.db.execute(query, params, fetchall=True)

    def dashboard_summary(self, actor: CurrentUser) -> dict[str, Any]:
        city_id = self._resolve_city_scope(actor, None)

        scope_filter = ""
        params: tuple[Any, ...] = ()
        if city_id is not None:
            scope_filter = " WHERE city_id = %s"
            params = (city_id,)

        apartments = self.db.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied,
                SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available
            FROM apartments
            {scope_filter}
            """,
            params,
            fetchone=True,
        )

        tenants = self.db.execute(
            f"SELECT COUNT(*) AS total FROM tenants{scope_filter}",
            params,
            fetchone=True,
        )

        where_invoice = ""
        invoice_params: tuple[Any, ...] = ()
        if city_id is not None:
            where_invoice = "WHERE a.city_id = %s"
            invoice_params = (city_id,)

        invoices = self.db.execute(
            f"""
            SELECT
                SUM(CASE WHEN i.status = 'LATE' THEN 1 ELSE 0 END) AS late_count,
                ROUND(COALESCE(SUM(CASE WHEN i.status = 'LATE' THEN i.amount ELSE 0 END), 0), 2) AS late_amount
            FROM invoices i
            JOIN leases l ON l.id = i.lease_id
            JOIN apartments a ON a.id = l.apartment_id
            {where_invoice}
            """,
            invoice_params,
            fetchone=True,
        )

        return {
            "apartments_total": int(apartments["total"] or 0),
            "apartments_occupied": int(apartments["occupied"] or 0),
            "apartments_available": int(apartments["available"] or 0),
            "tenants_total": int(tenants["total"] or 0),
            "late_invoices": int(invoices["late_count"] or 0),
            "late_amount": float(invoices["late_amount"] or 0),
            "actor": asdict(actor),
        }
