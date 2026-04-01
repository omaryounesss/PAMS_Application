"""Main entrypoint for the PAMS desktop application."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from app.config import load_app_config, load_database_config
from app.database import Database
from app.services import PamsService
from app.ui.app import PamsDesktopApp


def main() -> None:
    try:
        db_cfg = load_database_config()
        app_cfg = load_app_config()
        db = Database(db_cfg)
        service = PamsService(db, app_cfg)
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Startup error",
            f"Failed to initialise application.\n\n{exc}\n\n"
            "Ensure MySQL is running, mysql-connector-python is installed, "
            "and your database credentials are set in environment variables "
            "or in PAMS_Application/.env.",
        )
        root.destroy()
        return

    app = PamsDesktopApp(service, app_cfg)
    app.mainloop()


if __name__ == "__main__":
    main()
