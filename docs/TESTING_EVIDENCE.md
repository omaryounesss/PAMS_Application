# Testing Evidence (Manual + Automated)

## 1. Automated Testing

Command:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Observed result:

- `Ran 13 tests in 0.08s`
- `OK`

Test scope:

- password hashing and verification
- field validators (NI, email, phone, money, date order)
- core business rules (early-leave penalty, notice period, invoice lateness)
- tenant portal rule checks (card validation and tenant scope controls)

## 2. Manual Test Cases

| Case # | Description | Test Input | Expected Output | Actual Output | Evidence Screenshot |
|---:|---|---|---|---|---|
| 1 | Login screen loads | Open app start page | Username/password form appears | As expected | Login screen |
| 2 | Admin dashboard card values | Login as admin_cardiff | City-scoped summary cards update | As expected | Admin dashboard screenshot |
| 3 | Manager dashboard values | Login as manager_uk | Cross-city totals displayed | As expected | Manager dashboard screenshot |
| 4 | Tenant list display | Open Tenants tab | Existing tenants shown by scope | As expected | Tenants tab screenshot |
| 5 | Apartment list display | Open Apartments tab | Apartments with status/rent displayed | As expected | Apartments tab screenshot |
| 6 | Maintenance list display | Open Maintenance tab | Requests with status, cost, hours shown | As expected | Maintenance tab screenshot |
| 7 | Billing list display | Open Billing tab | Invoices show city/tenant/amount/status | As expected | Billing tab screenshot |
| 8 | Users and cities display | Open Users & Cities tab | User records visible to admin | As expected | Users & Cities screenshot |
| 9 | Multi-city manager scope | Login manager_uk | Sees 12 apartments and 12 tenants | As expected | Manager dashboard screenshot |
| 10 | City-admin scope restriction | Login admin_cardiff | Sees only Cardiff-scoped data | As expected | Admin dashboard + tenants screenshot |
| 11 | Add apartment action | Enter apartment form data | New apartment persisted and listed | Passed during manual run | Apartments tab |
| 12 | Request maintenance action | Create request in maintenance form | New row appears in maintenance list | Passed during manual run | Maintenance tab |
| 13 | Create invoice action | Enter lease/month/due/amount | New invoice row created | Passed during manual run | Billing tab |
| 14 | Record payment action | Enter invoice/payment fields | Invoice status updates paid/partial | Passed during manual run | Billing tab |
| 15 | Tenant early-leave action | Lease ID + requested date | Request captured; penalty rule applied | Passed during manual run | Tenants tab operations panel |
| 16 | Tenant portal payment flow | Tenant submits valid card payment | Success popup shown and invoice status updated | Passed | Tenant payment success screenshot |
| 17 | Tenant portal repair request | Tenant submits repair request | Request appears in tenant repair progress | Passed | Tenant repairs screenshot |
| 18 | Tenant portal complaint flow | Tenant submits complaint | Complaint is accepted and logged | Passed | Tenant complaints screenshot |

## 3. Integration Flow Tests

- Flow A: Register tenant -> create lease -> generate invoice -> record payment
- Flow B: Register maintenance request -> schedule -> resolve -> maintenance report
- Flow C: Add apartment -> occupancy reflected in report

All three flows were executed manually and validated using UI state changes and list views.

## 4. Screenshot Set Used as Evidence

- Login interface
- Manager dashboard with cross-city totals
- Admin dashboard with city-scoped totals
- Tenant management screen
- Apartment management screen
- Maintenance management screen
- Billing and payment screen
- User and city management screen
