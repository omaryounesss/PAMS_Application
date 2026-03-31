"""Application configuration for PAMS desktop app."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_name: str = "pams_pool"
    pool_size: int = 8


@dataclass(frozen=True)
class AppConfig:
    app_title: str = "Paragon Apartment Management System"
    lockout_minutes: int = 10
    max_failed_logins: int = 5


def load_database_config() -> DatabaseConfig:
    return DatabaseConfig(
        host=os.getenv("PAMS_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("PAMS_DB_PORT", "3306")),
        user=os.getenv("PAMS_DB_USER", "root"),
        password=os.getenv("PAMS_DB_PASSWORD", ""),
        database=os.getenv("PAMS_DB_NAME", "pams"),
        pool_name=os.getenv("PAMS_DB_POOL_NAME", "pams_pool"),
        pool_size=int(os.getenv("PAMS_DB_POOL_SIZE", "8")),
    )


def load_app_config() -> AppConfig:
    return AppConfig(
        app_title=os.getenv(
            "PAMS_APP_TITLE", "Paragon Apartment Management System (PAMS)"
        ),
        lockout_minutes=int(os.getenv("PAMS_LOCKOUT_MINUTES", "10")),
        max_failed_logins=int(os.getenv("PAMS_MAX_FAILED_LOGINS", "5")),
    )
