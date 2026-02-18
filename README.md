# Paragon Apartment Management System (PAMS)

Desktop application for `UFCF8S-30-2` built with `Tkinter + MySQL`, designed to align with the assessment brief.

## Features Implemented

- Role-based login and access control (`FRONT_DESK`, `FINANCE_MANAGER`, `MAINTENANCE_STAFF`, `ADMIN`, `MANAGER`, `TENANT`)
- Tenant registration and management
- Lease handling with early-leave workflow (1 month notice + 5% penalty)
- Complaint logging
- Apartment registration and occupancy tracking
- Maintenance lifecycle management (reported, scheduled, in progress, resolved)
- Invoice and payment emulation (receipt generation, overdue marking)
- Reports:
  - occupancy by city
  - financial summary (collected vs pending vs late)
  - maintenance cost tracking
- Tenant dashboard:
  - own payment records and late alerts
  - submit complaint and repair request
  - view repair progress
  - card payment emulation with card validation
  - graph views (payment history, neighbour comparison, late payments per property)
- Security baseline:
  - hashed passwords (PBKDF2)
  - account lockout on repeated failed logins
  - role-based authorization checks
  - audit logging
- Non-functional support:
  - indexed schema
  - connection pooling
  - scalable city model

## Project Structure

- `/app` application source code
- `/app/ui` Tkinter views and theming
- `/sql/schema.sql` schema definition
- `/scripts/bootstrap_db.py` schema + seed initializer
- `/tests` automated tests (unit level)
- `/docs` submission documents/templates
- `/docs/diagrams` safe diagram creation workbook

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure DB env vars (or use defaults in `.env.example`).
4. Ensure MySQL server is running and your user can create/use DB `pams`.
5. Initialize schema + seed:

```bash
python3 scripts/bootstrap_db.py
```

6. Run app:

```bash
python3 main.py
```

## Seed Login Accounts

- `admin_bristol / Admin@123`
- `frontdesk_bristol / Front@123`
- `finance_bristol / Finance@123`
- `maintenance_bristol / Maintain@123`
- `manager_uk / Manager@123`
- `admin_cardiff / Admin@123`
- `tenant_hamdy / Tenant@123`
- `tenant_younes / Tenant@123`
- `tenant_sharaf / Tenant@123`
- `tenant_nadine / Tenant@123`

## Run Automated Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Submission Notes

Use the docs folder to produce required portfolio files:

- `docs/diagrams/DIAGRAM_WORKBOOK.md` (you author final diagrams)
- `docs/AGILE_METHODOLOGY_REPORT.md`
- `docs/TESTING_EVIDENCE.md`
- `docs/CONTRIBUTION_LOG_TEMPLATE.md`
- `docs/DELIVERABLES_CHECKLIST.md`

Generated final PDFs:

- `docs/diagrams/PAMS_Diagrams_All_In_One.pdf`
- `docs/AGILE_METHODOLOGY_REPORT_FINAL.pdf`
- `docs/TESTING_EVIDENCE_FINAL.pdf`
- `docs/CONTRIBUTION_LOG_FINAL.pdf`

Build final submission package:

```bash
./scripts/build_final_submission.sh
```
