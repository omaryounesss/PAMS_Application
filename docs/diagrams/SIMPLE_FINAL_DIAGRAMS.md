# Simple Final Diagram Set (Spec-Focused)

This set is intentionally minimal and matches what the brief asks for:
- 1 Use Case diagram
- 1 Class diagram
- 3 Sequence diagrams

## 1) Use Case Diagram

```mermaid
flowchart LR
    FD[Front-desk Staff]
    FM[Finance Manager]
    MS[Maintenance Staff]
    AD[Administrator]
    MG[Manager]

    subgraph PAMS["PAMS System"]
        U1((Login))
        U2((Manage Tenants))
        U3((Manage Leases))
        U4((Manage Apartments))
        U5((Create/Track Maintenance Request))
        U6((Manage Invoices))
        U7((Record Payments))
        U8((Generate Occupancy Report))
        U9((Generate Financial Report))
        U10((Generate Maintenance Report))
        U11((Manage User Accounts))
        U12((Manage City Locations))
    end

    FD --> U1
    FD --> U2
    FD --> U3
    FD --> U5

    FM --> U1
    FM --> U6
    FM --> U7
    FM --> U9

    MS --> U1
    MS --> U5
    MS --> U10

    AD --> U1
    AD --> U2
    AD --> U3
    AD --> U4
    AD --> U5
    AD --> U6
    AD --> U7
    AD --> U8
    AD --> U9
    AD --> U10
    AD --> U11

    MG --> U1
    MG --> U8
    MG --> U9
    MG --> U10
    MG --> U12
```

## 2) Class Diagram

```mermaid
classDiagram
    class City {
      +id: int
      +name: string
    }

    class User {
      +id: int
      +username: string
      +fullName: string
      +role: string
      +cityId: int
    }

    class Tenant {
      +id: int
      +niNumber: string
      +firstName: string
      +lastName: string
      +phone: string
      +email: string
    }

    class Apartment {
      +id: int
      +code: string
      +type: string
      +rooms: int
      +monthlyRent: decimal
      +status: string
    }

    class Lease {
      +id: int
      +startDate: date
      +endDate: date
      +monthlyRent: decimal
      +deposit: decimal
      +status: string
    }

    class MaintenanceRequest {
      +id: int
      +title: string
      +priority: string
      +status: string
      +cost: decimal
    }

    class Invoice {
      +id: int
      +billingMonth: string
      +dueDate: date
      +amount: decimal
      +status: string
    }

    class Payment {
      +id: int
      +paidOn: date
      +amount: decimal
      +method: string
      +receiptNo: string
    }

    City "1" --> "*" User
    City "1" --> "*" Tenant
    City "1" --> "*" Apartment
    Tenant "1" --> "*" Lease
    Apartment "1" --> "*" Lease
    Apartment "1" --> "*" MaintenanceRequest
    Lease "1" --> "*" Invoice
    Invoice "1" --> "*" Payment
```

## 3) Sequence Diagram: Register Tenant + Lease

```mermaid
sequenceDiagram
    actor FrontDesk
    participant UI
    participant Service
    participant DB

    FrontDesk->>UI: Enter tenant + lease details
    UI->>Service: register_tenant(data)
    Service->>DB: Insert tenant
    DB-->>Service: tenantId
    Service->>DB: Create lease
    Service->>DB: Update apartment status (OCCUPIED)
    Service-->>UI: Success
    UI-->>FrontDesk: Show confirmation
```

## 4) Sequence Diagram: Invoice + Payment

```mermaid
sequenceDiagram
    actor FinanceManager
    participant UI
    participant Service
    participant DB

    FinanceManager->>UI: Create invoice
    UI->>Service: create_invoice(data)
    Service->>DB: Insert invoice
    Service-->>UI: Invoice created

    FinanceManager->>UI: Record payment
    UI->>Service: record_payment(data)
    Service->>DB: Insert payment
    Service->>DB: Update invoice status
    Service-->>UI: Payment recorded
```

## 5) Sequence Diagram: Resolve Maintenance Request

```mermaid
sequenceDiagram
    actor MaintenanceStaff
    participant UI
    participant Service
    participant DB

    MaintenanceStaff->>UI: Open request and submit resolution
    UI->>Service: update_maintenance(data)
    Service->>DB: Update maintenance request
    Service->>DB: Save cost/time/status
    Service-->>UI: Update successful
    UI-->>MaintenanceStaff: Show resolved status
```

