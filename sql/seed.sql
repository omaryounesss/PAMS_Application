USE pams;

INSERT INTO cities (id, name) VALUES
(1, 'Bristol'),
(2, 'Cardiff'),
(3, 'London'),
(4, 'Manchester');

-- Keep original login usernames and passwords
INSERT INTO users (username, full_name, role, city_id, password_hash, password_salt) VALUES
('admin_bristol', 'Omar Younes', 'ADMIN', 1, 'L+jRjylvt9VBaJty5Xb/FC8H70RiDA7BIzpCje1KD5Y=', 'CwDsvgb2f0cKGdCGXlAyNQ=='),
('frontdesk_bristol', 'Zain Sharaf', 'FRONT_DESK', 1, 'NsarkNKBagFxKtqKSpkOtMvP1MTGiSsaGi5tw5A4p8k=', 'LIcOIOY+VYuA2nJZW+89HQ=='),
('finance_bristol', 'Mohammed Hamdy', 'FINANCE_MANAGER', 1, 'ExrNRrPWTzU+vLA1SkfEKkxz6xanwyvu+MzcH/RsZzc=', 'gHlxKrawf75s8xvCAKxIkA=='),
('maintenance_bristol', 'Mohamed Alabweh', 'MAINTENANCE_STAFF', 1, '1x7AyqtUejjl39RQNyrawjU60GVda7EjjpDgzzRqyAw=', 'l/m6KRp96+gQJtD0jwkVKg=='),
('manager_uk', 'Omar Abdelatty', 'MANAGER', NULL, 'jY7CQkf79+3B3jHhE3FXEj0rG+cHmm3LKFQ1J63JPZE=', 'L3fRreaauQszFKyCB7tVrw=='),
('admin_cardiff', 'Omar Abdelatty', 'ADMIN', 2, '3FE6yV6QqravYNd7ZF39m1zA2VhMqbUi+wE3FJU7L4M=', 'TFuDmjeOFTIW6ahCRUXjZA==');

-- Larger apartment dataset for wider testing
INSERT INTO apartments (city_id, code, address, apartment_type, rooms, monthly_rent, status) VALUES
(1, 'BRS-101', '1 King Street, Bristol', 'Two Bedroom Flat', 2, 1250.00, 'AVAILABLE'),
(1, 'BRS-102', '2 King Street, Bristol', 'One Bedroom Flat', 1, 950.00, 'AVAILABLE'),
(1, 'BRS-103', '5 Riverside Walk, Bristol', 'Studio', 1, 875.00, 'AVAILABLE'),
(2, 'CDF-201', '10 Castle Road, Cardiff', 'Two Bedroom Flat', 2, 1180.00, 'AVAILABLE'),
(2, 'CDF-202', '22 Castle Road, Cardiff', 'Three Bedroom Flat', 3, 1500.00, 'AVAILABLE'),
(2, 'CDF-203', '4 Bay View, Cardiff', 'One Bedroom Flat', 1, 980.00, 'AVAILABLE'),
(3, 'LON-301', '8 Station Road, London', 'Studio', 1, 1600.00, 'AVAILABLE'),
(3, 'LON-302', '14 Elm Court, London', 'Two Bedroom Flat', 2, 2100.00, 'AVAILABLE'),
(3, 'LON-303', '42 West Bridge, London', 'One Bedroom Flat', 1, 1750.00, 'AVAILABLE'),
(4, 'MAN-401', '4 River View, Manchester', 'Three Bedroom Flat', 3, 1450.00, 'AVAILABLE'),
(4, 'MAN-402', '17 North Lane, Manchester', 'Two Bedroom Flat', 2, 1250.00, 'AVAILABLE'),
(4, 'MAN-403', '9 Market Way, Manchester', 'One Bedroom Flat', 1, 1100.00, 'AVAILABLE');

-- Tenants include your group names + more records for testing
INSERT INTO tenants (
    city_id, ni_number, first_name, last_name, phone, email,
    occupation, references_text, required_apartment_type, created_by
) VALUES
(1, 'AB123456C', 'Mohammed', 'Hamdy', '+44 7900 111111', 'mohammed.hamdy@example.com',
 'Accountant', 'Employer and previous landlord references verified', 'Two Bedroom Flat', 2),
(1, 'CH234567D', 'Mohamed', 'Alabweh', '+44 7900 111112', 'mohamed.alabweh@example.com',
 'Graphic Designer', 'Guarantor and payslips checked', 'One Bedroom Flat', 2),
(2, 'JK345678A', 'Omar', 'Younes', '+44 7900 111113', 'omar.younes@example.com',
 'Software Engineer', 'Bank statements and tenancy history reviewed', 'Two Bedroom Flat', 6),
(2, 'LM456789B', 'Zain', 'Sharaf', '+44 7900 111114', 'zain.sharaf@example.com',
 'Business Analyst', 'References approved after call verification', 'Three Bedroom Flat', 6),
(3, 'NP567890C', 'Omar', 'Abdelatty', '+44 7900 111115', 'omar.abdelatty@example.com',
 'Consultant', 'Employment contract and previous tenancy checked', 'Studio', 1),
(3, 'RT678901D', 'Kareem', 'Hassan', '+44 7900 111116', 'kareem.hassan@example.com',
 'Project Manager', 'Credit check clear, references valid', 'Two Bedroom Flat', 1),
(4, 'WX789012A', 'Yousef', 'Nasser', '+44 7900 111117', 'yousef.nasser@example.com',
 'Data Analyst', 'Landlord reference and income evidence accepted', 'Three Bedroom Flat', 1),
(4, 'YA890123B', 'Mariam', 'Fathy', '+44 7900 111118', 'mariam.fathy@example.com',
 'Teacher', 'References and right-to-rent documents verified', 'One Bedroom Flat', 1),
(1, 'ZE901234C', 'Omar', 'Abdelatty', '+44 7900 111119', 'omar.abdelatty.tenant@example.com',
 'Nurse', 'Application pending final approval', 'Studio', 2),
(3, 'MN112233B', 'Nadine', 'Elgamal', '+44 7900 111121', 'nadine.elgamal@example.com',
 'Marketing Specialist', 'Employment letter and previous tenancy references verified', 'One Bedroom Flat', 1),
(2, 'GH012345D', 'Nour', 'Eldin', '+44 7900 111120', 'nour.eldin@example.com',
 'Architect', 'Application pending apartment allocation', 'Two Bedroom Flat', 6);

-- Tenant portal users (password for all: Tenant@123)
INSERT INTO users (username, full_name, role, city_id, password_hash, password_salt) VALUES
('tenant_hamdy', 'Mohammed Hamdy', 'TENANT', 1, 'kbiiUhaFO047ujrojWFIF7coMGeKSZ8OY+UFNmIzLVI=', 'tqrVi64fl/VwIaIsf5dYig=='),
('tenant_alabweh', 'Mohamed Alabweh', 'TENANT', 1, 'kbiiUhaFO047ujrojWFIF7coMGeKSZ8OY+UFNmIzLVI=', 'tqrVi64fl/VwIaIsf5dYig=='),
('tenant_younes', 'Omar Younes', 'TENANT', 2, 'UAsCuQOdSlBTUy4zwPzKGlHMAB4vCQE7UfxMRdpUipI=', 'oIV+ORbttX4fTvT5DhfaSQ=='),
('tenant_sharaf', 'Zain Sharaf', 'TENANT', 2, 'WqLTDjbYaGa7EXctRYonqNenkopEhGMlkkRfiAbkfF0=', '5BaGbmX31ESsaHVCxMo5vA=='),
('tenant_nadine', 'Nadine Elgamal', 'TENANT', 3, 'zLkngvluaItAWD8TIuihM4cY7HsNjfPr30fRzEfIbfA=', 'ULDCbT6U+6fBqc7IMni40g=='),
('tenant_yousef', 'Yousef Nasser', 'TENANT', 4, 'kbiiUhaFO047ujrojWFIF7coMGeKSZ8OY+UFNmIzLVI=', 'tqrVi64fl/VwIaIsf5dYig=='),
('tenant_mariam', 'Mariam Fathy', 'TENANT', 4, 'kbiiUhaFO047ujrojWFIF7coMGeKSZ8OY+UFNmIzLVI=', 'tqrVi64fl/VwIaIsf5dYig=='),
('tenant_nour', 'Nour Eldin', 'TENANT', 2, 'kbiiUhaFO047ujrojWFIF7coMGeKSZ8OY+UFNmIzLVI=', 'tqrVi64fl/VwIaIsf5dYig==');

INSERT INTO tenant_accounts (user_id, tenant_id) VALUES
((SELECT id FROM users WHERE username = 'tenant_hamdy'), (SELECT id FROM tenants WHERE ni_number = 'AB123456C')),
((SELECT id FROM users WHERE username = 'tenant_alabweh'), (SELECT id FROM tenants WHERE ni_number = 'CH234567D')),
((SELECT id FROM users WHERE username = 'tenant_younes'), (SELECT id FROM tenants WHERE ni_number = 'JK345678A')),
((SELECT id FROM users WHERE username = 'tenant_sharaf'), (SELECT id FROM tenants WHERE ni_number = 'LM456789B')),
((SELECT id FROM users WHERE username = 'tenant_nadine'), (SELECT id FROM tenants WHERE ni_number = 'MN112233B')),
((SELECT id FROM users WHERE username = 'tenant_yousef'), (SELECT id FROM tenants WHERE ni_number = 'WX789012A')),
((SELECT id FROM users WHERE username = 'tenant_mariam'), (SELECT id FROM tenants WHERE ni_number = 'YA890123B')),
((SELECT id FROM users WHERE username = 'tenant_nour'), (SELECT id FROM tenants WHERE ni_number = 'GH012345D'));

INSERT INTO leases (
    tenant_id, apartment_id, start_date, end_date, requested_end_date, notice_given_date,
    monthly_rent, deposit_amount, early_leave_penalty, status
) VALUES
(1, 1, '2026-01-01', '2026-12-31', NULL, NULL, 1250.00, 1250.00, 0.00, 'ACTIVE'),
(2, 2, '2026-01-10', '2026-11-30', NULL, NULL, 950.00, 950.00, 0.00, 'ACTIVE'),
(3, 4, '2026-01-15', '2026-12-14', NULL, NULL, 1180.00, 1180.00, 0.00, 'ACTIVE'),
(4, 5, '2026-01-20', '2026-12-19', '2026-11-20', '2026-10-18', 1500.00, 1500.00, 75.00, 'EARLY_LEAVE_REQUESTED'),
(5, 7, '2026-02-01', '2026-11-30', NULL, NULL, 1600.00, 1600.00, 0.00, 'ACTIVE'),
(6, 8, '2025-05-01', '2026-01-31', NULL, NULL, 2100.00, 2100.00, 0.00, 'ENDED'),
(7, 10, '2026-01-05', '2026-12-04', NULL, NULL, 1450.00, 1450.00, 0.00, 'ACTIVE'),
(8, 11, '2026-02-03', '2027-02-02', NULL, NULL, 1250.00, 1250.00, 0.00, 'ACTIVE'),
(10, 9, '2026-02-10', '2027-02-09', NULL, NULL, 1750.00, 1750.00, 0.00, 'ACTIVE'),
(11, 6, '2026-02-06', '2027-02-05', NULL, NULL, 980.00, 980.00, 0.00, 'ACTIVE');

UPDATE apartments SET status = 'OCCUPIED' WHERE id IN (1, 2, 4, 5, 6, 7, 9, 10, 11);
UPDATE apartments SET status = 'MAINTENANCE' WHERE id IN (3);

INSERT INTO invoices (lease_id, billing_month, due_date, amount, status, created_by) VALUES
(1, '2026-01', '2026-01-05', 1250.00, 'PAID', 3),
(1, '2026-02', '2026-02-05', 1250.00, 'LATE', 3),
(2, '2026-01', '2026-01-12', 950.00, 'PAID', 3),
(2, '2026-02', '2026-02-12', 950.00, 'PARTIAL', 3),
(3, '2026-01', '2026-01-20', 1180.00, 'PAID', 3),
(3, '2026-02', '2026-02-20', 1180.00, 'PENDING', 3),
(4, '2026-02', '2026-02-22', 1500.00, 'PAID', 3),
(4, '2026-03', '2026-03-22', 75.00, 'PENDING', 3),
(5, '2026-02', '2026-02-07', 1600.00, 'PAID', 3),
(7, '2026-02', '2026-02-10', 1450.00, 'LATE', 3),
(8, '2026-02', '2026-02-12', 1250.00, 'PENDING', 3),
(7, '2026-01', '2026-01-10', 1450.00, 'PAID', 3),
(9, '2026-02', '2026-02-22', 1750.00, 'LATE', 3),
(9, '2026-03', '2026-03-22', 1750.00, 'PENDING', 3),
(1, '2026-03', '2026-03-05', 1250.00, 'PENDING', 3),
(2, '2026-03', '2026-03-12', 950.00, 'PAID', 3),
(3, '2026-03', '2026-03-20', 1180.00, 'PARTIAL', 3),
(5, '2026-03', '2026-03-07', 1600.00, 'PENDING', 3),
(7, '2026-03', '2026-03-10', 1450.00, 'PAID', 3),
(8, '2026-03', '2026-03-12', 1250.00, 'PARTIAL', 3),
(9, '2026-04', '2026-04-22', 1750.00, 'PENDING', 3),
(10, '2026-02', '2026-02-18', 980.00, 'PAID', 3),
(10, '2026-03', '2026-03-18', 980.00, 'PENDING', 3);

INSERT INTO payments (invoice_id, amount, paid_on, method, recorded_by, receipt_no) VALUES
(1, 1250.00, '2026-01-03', 'BANK_TRANSFER', 3, 'RCT-0001-SEED'),
(3, 950.00, '2026-01-11', 'CARD', 3, 'RCT-0003-SEED'),
(4, 500.00, '2026-02-13', 'BANK_TRANSFER', 3, 'RCT-0004-SEED'),
(5, 1180.00, '2026-01-18', 'BANK_TRANSFER', 3, 'RCT-0005-SEED'),
(7, 1500.00, '2026-02-20', 'CARD', 3, 'RCT-0007-SEED'),
(9, 1600.00, '2026-02-05', 'CARD', 3, 'RCT-0009-SEED'),
(12, 1450.00, '2026-01-09', 'BANK_TRANSFER', 3, 'RCT-0012-SEED'),
(16, 950.00, '2026-03-11', 'CARD', 3, 'RCT-0016-SEED'),
(17, 600.00, '2026-03-18', 'BANK_TRANSFER', 3, 'RCT-0017-SEED'),
(19, 1450.00, '2026-03-09', 'BANK_TRANSFER', 3, 'RCT-0019-SEED'),
(20, 400.00, '2026-03-11', 'CARD', 3, 'RCT-0020-SEED'),
(22, 980.00, '2026-02-17', 'BANK_TRANSFER', 3, 'RCT-0022-SEED');

UPDATE invoices SET paid_at='2026-01-03' WHERE id=1;
UPDATE invoices SET paid_at='2026-01-11' WHERE id=3;
UPDATE invoices SET paid_at='2026-02-13' WHERE id=4;
UPDATE invoices SET paid_at='2026-01-18' WHERE id=5;
UPDATE invoices SET paid_at='2026-02-20' WHERE id=7;
UPDATE invoices SET paid_at='2026-02-05' WHERE id=9;
UPDATE invoices SET paid_at='2026-01-09' WHERE id=12;
UPDATE invoices SET paid_at='2026-03-11' WHERE id=16;
UPDATE invoices SET paid_at='2026-03-18' WHERE id=17;
UPDATE invoices SET paid_at='2026-03-09' WHERE id=19;
UPDATE invoices SET paid_at='2026-03-11' WHERE id=20;
UPDATE invoices SET paid_at='2026-02-17' WHERE id=22;

INSERT INTO complaints (tenant_id, title, description, status, created_by) VALUES
(1, 'Noise from corridor', 'Repeated late-night noise near apartment entrance.', 'OPEN', 2),
(2, 'Intercom issue', 'Building intercom not functioning properly.', 'IN_REVIEW', 2),
(4, 'Parking concern', 'Visitor parking spaces are frequently blocked.', 'OPEN', 6),
(5, 'Lift delay', 'Lift response time is very slow at peak hours.', 'RESOLVED', 1),
(7, 'Heating schedule', 'Heating timer not matching tenant setting.', 'IN_REVIEW', 1),
(8, 'Window insulation', 'Cold air entering through bedroom window frame.', 'CLOSED', 1),
(10, 'Service charge query', 'Would like a breakdown of the latest service charge.', 'OPEN', 1),
(11, 'Parcel storage', 'Reception parcel shelf is full at peak times.', 'IN_REVIEW', 6),
(3, 'Bike storage access', 'Bike storage lock sometimes jams in the morning.', 'RESOLVED', 6),
(6, 'Water pressure variation', 'Kitchen tap pressure drops in the evening.', 'CLOSED', 1);

INSERT INTO maintenance_requests (
    apartment_id, tenant_id, title, description, priority, status,
    requested_by, resolved_by, scheduled_at, resolved_at, resolution_notes, time_spent_hours, cost
) VALUES
(1, 1, 'Boiler pressure drop', 'Boiler pressure drops overnight and needs refill.', 'HIGH', 'SCHEDULED', 2, NULL, '2026-02-20', NULL, NULL, 0.00, 0.00),
(2, 2, 'Leaking kitchen tap', 'Constant tap drip causing water waste.', 'MEDIUM', 'RESOLVED', 2, 4, '2026-02-10', '2026-02-11', 'Washer replaced and leak test passed.', 1.50, 65.00),
(3, NULL, 'Hallway lighting fault', 'Shared corridor lights flicker intermittently.', 'LOW', 'REPORTED', 1, NULL, NULL, NULL, NULL, 0.00, 0.00),
(4, 3, 'Bathroom extractor fan', 'Extractor fan stopped working.', 'MEDIUM', 'IN_PROGRESS', 6, NULL, '2026-02-16', NULL, 'Motor unit being replaced.', 0.75, 25.00),
(5, 4, 'Radiator valve issue', 'One radiator remains cold despite thermostat setting.', 'HIGH', 'SCHEDULED', 6, NULL, '2026-02-18', NULL, NULL, 0.00, 0.00),
(7, 5, 'Door lock stiffness', 'Main door lock is difficult to turn.', 'MEDIUM', 'RESOLVED', 1, 4, '2026-02-08', '2026-02-08', 'Lock cylinder lubricated and aligned.', 1.00, 40.00),
(10, 7, 'Ceiling stain inspection', 'Possible leak mark visible in bedroom corner.', 'HIGH', 'IN_PROGRESS', 1, NULL, '2026-02-17', NULL, 'Plumbing check in progress.', 1.25, 55.00),
(11, 8, 'Balcony door seal', 'Seal gap causes draft and rain splash.', 'LOW', 'REPORTED', 1, NULL, NULL, NULL, NULL, 0.00, 0.00),
(6, 11, 'Shower mixer fault', 'Shower temperature keeps fluctuating after five minutes.', 'MEDIUM', 'SCHEDULED', 6, NULL, '2026-02-22', NULL, NULL, 0.00, 0.00),
(9, 10, 'Bedroom blind track', 'Blind track is loose and scraping the frame.', 'LOW', 'REPORTED', 1, NULL, NULL, NULL, NULL, 0.00, 0.00),
(9, 10, 'Extractor vent noise', 'Vent rattles loudly during windy evenings.', 'MEDIUM', 'IN_PROGRESS', 1, NULL, '2026-03-04', NULL, 'External cover inspection booked.', 0.50, 18.00),
(6, 11, 'Entry buzzer volume', 'Intercom buzzer volume is too low to hear from kitchen.', 'LOW', 'RESOLVED', 6, 4, '2026-02-14', '2026-02-14', 'Receiver unit adjusted and tested.', 0.75, 22.00),
(11, 8, 'Bathroom seal renewal', 'Bath edge silicone seal has started to peel.', 'MEDIUM', 'SCHEDULED', 1, NULL, '2026-03-06', NULL, NULL, 0.00, 0.00);
