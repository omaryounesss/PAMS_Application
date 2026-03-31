# Diagram Workbook (Submission-Safe, Student-Authored)

This workbook is designed so **you create the final design artifacts yourself**.

The module brief says AI can help code snippets but not design; this file gives structure, checks, and prompts only.

## Deliverables Required

- 1 Use Case Diagram
- 1 Class Diagram
- At least 3 Sequence Diagrams (one use case each)
- All in one single PDF for submission

## Step 1: Use Case Diagram (You Draw)

### Actors to include

- Front-desk Staff
- Finance Manager
- Maintenance Staff
- Administrator (city-level)
- Manager (cross-city)

### Use case checklist

- [ ] Authenticate user
- [ ] Register tenant
- [ ] Update tenant details
- [ ] Track lease agreements
- [ ] Submit complaint
- [ ] Log maintenance request
- [ ] Update maintenance resolution
- [ ] Register apartment
- [ ] Assign apartment/track occupancy
- [ ] Create invoice
- [ ] Record payment
- [ ] Mark late payments
- [ ] Generate occupancy report
- [ ] Generate financial summary
- [ ] Generate maintenance cost report
- [ ] Manage users (admin)
- [ ] Add city/location (manager)

### Quality checks

- [ ] Every actor has at least one use case
- [ ] No orphan use case
- [ ] Include/extend relations only where meaningful
- [ ] Diagram readable at one-page scale

## Step 2: Class Diagram (You Draw)

### Candidate classes from implementation

- User
- City
- Tenant
- Apartment
- Lease
- Complaint
- MaintenanceRequest
- Invoice
- Payment
- AuditLog
- PamsService

### Relationship checklist

- [ ] City 1..* Apartments
- [ ] City 1..* Users
- [ ] City 1..* Tenants
- [ ] Tenant 1..* Leases
- [ ] Apartment 1..* Leases
- [ ] Lease 1..* Invoices
- [ ] Invoice 0..* Payments
- [ ] Tenant 0..* Complaints
- [ ] Apartment 0..* MaintenanceRequests

### Attribute/method quality checks

- [ ] Use proper visibility (`+`, `-`)
- [ ] Use realistic data types
- [ ] Keep class names singular
- [ ] Add key operations (create, update, list, validate)

## Step 3: Sequence Diagrams (You Draw)

Create at least 3. Recommended scenarios:

1. Front-desk registers tenant with lease assignment
2. Finance manager generates invoice and records payment
3. Maintenance staff resolves maintenance request

### Sequence quality checks

- [ ] One use case per diagram
- [ ] Lifelines named consistently
- [ ] Message directions are correct
- [ ] Activation bars used clearly
- [ ] Return messages included where useful

## Suggested Diagram Tooling

- draw.io / diagrams.net
- Lucidchart
- Visual Paradigm

## Export Workflow

1. Draw each diagram as separate page/canvas.
2. Verify readability and labels.
3. Export all diagrams into one PDF file.
4. Name file clearly (example: `GroupX_DesignDiagrams.pdf`).

## Self-Declaration Tips for Viva

Be ready to explain:

- Why each actor has those permissions
- Why entities are related as drawn
- Why sequence message order is correct
- How diagrams trace to implemented features

