# Visual Diagram Pack (Draft)

These are visual drafts you can view directly in Markdown (Mermaid-rendered).

## 1) Use Case Diagram

```mermaid
flowchart LR
    FD[Front-desk Staff]
    FM[Finance Manager]
    MS[Maintenance Staff]
    AD[Administrator (City)]
    MG[Manager (All Cities)]

    subgraph SYS["Paragon Apartment Management System (PAMS)"]
        UC0((Authenticate User))
        UC1((Register / Update Tenant))
        UC2((Track Lease Agreements))
        UC3((Request Early Leave))
        UC4((Log Complaint))
        UC5((Register Apartment))
        UC6((Assign Apartment / Track Occupancy))
        UC7((Create Maintenance Request))
        UC8((Schedule / Resolve Maintenance))
        UC9((Create Invoice))
        UC10((Record Payment))
        UC11((Mark Late Payments))
        UC12((Generate Occupancy Report))
        UC13((Generate Financial Summary))
        UC14((Generate Maintenance Cost Report))
        UC15((Manage User Accounts))
        UC16((Add / Manage City Locations))
    end

    FD --> UC0
    FD --> UC1
    FD --> UC2
    FD --> UC4
    FD --> UC7

    FM --> UC0
    FM --> UC9
    FM --> UC10
    FM --> UC11
    FM --> UC13

    MS --> UC0
    MS --> UC8
    MS --> UC14

    AD --> UC0
    AD --> UC1
    AD --> UC2
    AD --> UC5
    AD --> UC6
    AD --> UC7
    AD --> UC8
    AD --> UC9
    AD --> UC10
    AD --> UC12
    AD --> UC13
    AD --> UC14
    AD --> UC15
    AD --> UC3

    MG --> UC0
    MG --> UC12
    MG --> UC13
    MG --> UC14
    MG --> UC16
```

## 2) Class Diagram

```mermaid
classDiagram
    class City {
      +int id
      +string name
      +bool isActive
    }

    class User {
      +int id
      +string username
      +string fullName
      +string role
      +int cityId
      +bool isActive
    }

    class Apartment {
      +int id
      +int cityId
      +string code
      +string address
      +string apartmentType
      +int rooms
      +decimal monthlyRent
      +string status
    }

    class Tenant {
      +int id
      +int cityId
      +string niNumber
      +string firstName
      +string lastName
      +string phone
      +string email
      +string occupation
      +bool isActive
    }

    class Lease {
      +int id
      +int tenantId
      +int apartmentId
      +date startDate
      +date endDate
      +decimal monthlyRent
      +decimal depositAmount
      +decimal earlyLeavePenalty
      +string status
    }

    class Complaint {
      +int id
      +int tenantId
      +string title
      +string description
      +string status
    }

    class MaintenanceRequest {
      +int id
      +int apartmentId
      +int tenantId
      +string title
      +string priority
      +string status
      +date scheduledAt
      +date resolvedAt
      +decimal timeSpentHours
      +decimal cost
    }

    class Invoice {
      +int id
      +int leaseId
      +string billingMonth
      +date dueDate
      +decimal amount
      +string status
      +date paidAt
    }

    class Payment {
      +int id
      +int invoiceId
      +decimal amount
      +date paidOn
      +string method
      +string receiptNo
    }

    class AuditLog {
      +long id
      +int userId
      +string action
      +string entity
      +int entityId
      +string details
    }

    class PamsService {
      +authenticate()
      +registerTenant()
      +createApartment()
      +createMaintenanceRequest()
      +updateMaintenance()
      +createInvoice()
      +recordPayment()
      +reportOccupancy()
      +reportFinancial()
      +reportMaintenanceCost()
    }

    City "1" --> "*" User : scopes
    City "1" --> "*" Apartment : contains
    City "1" --> "*" Tenant : contains
    Tenant "1" --> "*" Lease : has
    Apartment "1" --> "*" Lease : assigned in
    Tenant "1" --> "*" Complaint : raises
    Apartment "1" --> "*" MaintenanceRequest : has
    Lease "1" --> "*" Invoice : billed by
    Invoice "1" --> "*" Payment : paid by
    User "1" --> "*" AuditLog : creates
    PamsService ..> User
    PamsService ..> Tenant
    PamsService ..> Apartment
    PamsService ..> Lease
    PamsService ..> MaintenanceRequest
    PamsService ..> Invoice
    PamsService ..> Payment
```

## 3) Sequence Diagram A: Register Tenant + Lease Assignment

```mermaid
sequenceDiagram
    actor FrontDesk
    participant UI as Tkinter UI
    participant Service as PamsService
    participant DB as MySQL

    FrontDesk->>UI: Submit tenant form + lease details
    UI->>Service: register_tenant(data)
    Service->>Service: Validate NI/email/phone/date/rent
    Service->>DB: INSERT tenant
    DB-->>Service: tenant_id
    Service->>DB: SELECT apartment availability
    DB-->>Service: apartment status
    Service->>DB: INSERT lease
    Service->>DB: UPDATE apartment status=OCCUPIED
    Service->>DB: INSERT audit_log
    Service-->>UI: Success + tenant_id
    UI-->>FrontDesk: Show confirmation
```

## 4) Sequence Diagram B: Create Invoice + Record Payment

```mermaid
sequenceDiagram
    actor FinanceManager
    participant UI as Tkinter UI
    participant Service as PamsService
    participant DB as MySQL

    FinanceManager->>UI: Create invoice (lease, month, due, amount)
    UI->>Service: create_invoice(...)
    Service->>DB: Validate lease + city scope
    Service->>DB: INSERT invoice status=PENDING
    Service->>DB: INSERT audit_log
    Service-->>UI: invoice_id created

    FinanceManager->>UI: Record payment (invoice, amount, method, date)
    UI->>Service: record_payment(...)
    Service->>DB: SELECT invoice
    DB-->>Service: invoice amount/status
    Service->>DB: INSERT payment + receipt_no
    Service->>DB: UPDATE invoice status=PAID/PARTIAL
    Service->>DB: INSERT audit_log
    Service-->>UI: payment_id created
    UI-->>FinanceManager: Show receipt reference
```

## 5) Sequence Diagram C: Resolve Maintenance Request

```mermaid
sequenceDiagram
    actor MaintStaff as Maintenance Staff
    participant UI as Tkinter UI
    participant Service as PamsService
    participant DB as MySQL

    MaintStaff->>UI: Open request and enter update
    UI->>Service: update_maintenance(request_id, status, notes, hours, cost)
    Service->>DB: SELECT request + city scope check
    DB-->>Service: request found
    Service->>Service: Validate status/hours/cost/date
    alt status == RESOLVED
        Service->>DB: UPDATE request resolved_at=today, cost, hours
    else status != RESOLVED
        Service->>DB: UPDATE request status/scheduled data
    end
    Service->>DB: INSERT audit_log
    Service-->>UI: Update successful
    UI-->>MaintStaff: Show updated lifecycle state
```

