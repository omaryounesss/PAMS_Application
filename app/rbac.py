"""Role-based access control policy."""

from __future__ import annotations

from dataclasses import dataclass


ROLE_FRONT_DESK = "FRONT_DESK"
ROLE_FINANCE_MANAGER = "FINANCE_MANAGER"
ROLE_MAINTENANCE_STAFF = "MAINTENANCE_STAFF"
ROLE_ADMIN = "ADMIN"
ROLE_MANAGER = "MANAGER"
ROLE_TENANT = "TENANT"

ALL_ROLES = {
    ROLE_FRONT_DESK,
    ROLE_FINANCE_MANAGER,
    ROLE_MAINTENANCE_STAFF,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_TENANT,
}

PERMISSIONS: dict[str, set[str]] = {
    ROLE_FRONT_DESK: {
        "tenant:create",
        "tenant:update",
        "tenant:view",
        "lease:create",
        "lease:view",
        "lease:update",
        "complaint:create",
        "complaint:view",
        "maintenance:create",
        "maintenance:view",
        "apartment:view",
    },
    ROLE_FINANCE_MANAGER: {
        "invoice:create",
        "invoice:view",
        "payment:record",
        "payment:view",
        "report:financial",
        "tenant:view",
        "lease:view",
    },
    ROLE_MAINTENANCE_STAFF: {
        "maintenance:view",
        "maintenance:update",
        "report:maintenance",
    },
    ROLE_ADMIN: {
        "user:create",
        "user:update",
        "user:view",
        "tenant:create",
        "tenant:update",
        "tenant:view",
        "tenant:delete",
        "apartment:create",
        "apartment:update",
        "apartment:view",
        "apartment:delete",
        "lease:create",
        "lease:update",
        "lease:view",
        "complaint:view",
        "complaint:create",
        "maintenance:create",
        "maintenance:update",
        "maintenance:view",
        "invoice:create",
        "invoice:view",
        "payment:record",
        "payment:view",
        "report:financial",
        "report:occupancy",
        "report:maintenance",
        "city:create",
    },
    ROLE_MANAGER: {
        "report:financial",
        "report:occupancy",
        "report:maintenance",
        "apartment:view",
        "tenant:view",
        "lease:view",
        "city:create",
        "city:view",
    },
    ROLE_TENANT: {
        "tenant_portal:view",
        "tenant:own_payments:view",
        "tenant:own_late_alerts:view",
        "tenant:own_complaint:create",
        "tenant:own_repair:create",
        "tenant:own_repair:view",
        "tenant:own_payment:record",
        "tenant:own_graph:view",
    },
}


@dataclass(frozen=True)
class CurrentUser:
    id: int
    username: str
    full_name: str
    role: str
    city_id: int | None
    tenant_id: int | None


class AuthorizationError(PermissionError):
    pass


def can(role: str, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, set())


def require_permission(user: CurrentUser, permission: str) -> None:
    if not can(user.role, permission):
        raise AuthorizationError(
            f"User '{user.username}' with role '{user.role}' cannot '{permission}'"
        )
