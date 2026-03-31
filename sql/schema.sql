CREATE DATABASE IF NOT EXISTS pams;
USE pams;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS maintenance_requests;
DROP TABLE IF EXISTS complaints;
DROP TABLE IF EXISTS leases;
DROP TABLE IF EXISTS tenant_accounts;
DROP TABLE IF EXISTS tenants;
DROP TABLE IF EXISTS apartments;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS cities;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE cities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(60) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    role ENUM('FRONT_DESK', 'FINANCE_MANAGER', 'MAINTENANCE_STAFF', 'ADMIN', 'MANAGER', 'TENANT') NOT NULL,
    city_id INT NULL,
    password_hash VARCHAR(120) NOT NULL,
    password_salt VARCHAR(80) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until DATETIME NULL,
    last_login DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_city FOREIGN KEY (city_id) REFERENCES cities(id)
) ENGINE=InnoDB;

CREATE TABLE apartments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    code VARCHAR(30) NOT NULL,
    address VARCHAR(255) NOT NULL,
    apartment_type VARCHAR(60) NOT NULL,
    rooms INT NOT NULL,
    monthly_rent DECIMAL(10, 2) NOT NULL,
    status ENUM('AVAILABLE', 'OCCUPIED', 'MAINTENANCE', 'INACTIVE') NOT NULL DEFAULT 'AVAILABLE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_apartment_city_code UNIQUE (city_id, code),
    CONSTRAINT fk_apartment_city FOREIGN KEY (city_id) REFERENCES cities(id)
) ENGINE=InnoDB;

CREATE TABLE tenants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    ni_number VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(120) NOT NULL,
    occupation VARCHAR(80) NOT NULL,
    references_text TEXT,
    required_apartment_type VARCHAR(60) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tenant_city FOREIGN KEY (city_id) REFERENCES cities(id),
    CONSTRAINT fk_tenant_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE tenant_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    tenant_id INT NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tenant_accounts_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_tenant_accounts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
) ENGINE=InnoDB;

CREATE TABLE leases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    apartment_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    requested_end_date DATE NULL,
    notice_given_date DATE NULL,
    monthly_rent DECIMAL(10, 2) NOT NULL,
    deposit_amount DECIMAL(10, 2) NOT NULL,
    early_leave_penalty DECIMAL(10, 2) NOT NULL DEFAULT 0,
    status ENUM('ACTIVE', 'ENDED', 'EARLY_LEAVE_REQUESTED', 'EARLY_ENDED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_lease_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_lease_apartment FOREIGN KEY (apartment_id) REFERENCES apartments(id)
) ENGINE=InnoDB;

CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    title VARCHAR(140) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED') NOT NULL DEFAULT 'OPEN',
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    resolution_notes TEXT NULL,
    CONSTRAINT fk_complaint_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_complaint_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE maintenance_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apartment_id INT NOT NULL,
    tenant_id INT NULL,
    title VARCHAR(140) NOT NULL,
    description TEXT NOT NULL,
    priority ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL DEFAULT 'MEDIUM',
    status ENUM('REPORTED', 'SCHEDULED', 'IN_PROGRESS', 'RESOLVED') NOT NULL DEFAULT 'REPORTED',
    requested_by INT NOT NULL,
    resolved_by INT NULL,
    scheduled_at DATE NULL,
    resolved_at DATE NULL,
    resolution_notes TEXT NULL,
    time_spent_hours DECIMAL(8, 2) NOT NULL DEFAULT 0,
    cost DECIMAL(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_maintenance_apartment FOREIGN KEY (apartment_id) REFERENCES apartments(id),
    CONSTRAINT fk_maintenance_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_maintenance_requested_by FOREIGN KEY (requested_by) REFERENCES users(id),
    CONSTRAINT fk_maintenance_resolved_by FOREIGN KEY (resolved_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lease_id INT NOT NULL,
    billing_month CHAR(7) NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('PENDING', 'PARTIAL', 'PAID', 'LATE') NOT NULL DEFAULT 'PENDING',
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at DATE NULL,
    CONSTRAINT fk_invoice_lease FOREIGN KEY (lease_id) REFERENCES leases(id),
    CONSTRAINT fk_invoice_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    paid_on DATE NOT NULL,
    method VARCHAR(40) NOT NULL,
    recorded_by INT NOT NULL,
    receipt_no VARCHAR(40) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payment_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    CONSTRAINT fk_payment_user FOREIGN KEY (recorded_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(40) NOT NULL,
    entity VARCHAR(60) NOT NULL,
    entity_id INT NULL,
    details VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE INDEX idx_users_role_city ON users(role, city_id);
CREATE INDEX idx_tenants_city ON tenants(city_id);
CREATE INDEX idx_tenant_accounts_tenant ON tenant_accounts(tenant_id);
CREATE INDEX idx_apartments_city_status ON apartments(city_id, status);
CREATE INDEX idx_leases_apartment_status ON leases(apartment_id, status);
CREATE INDEX idx_invoices_status_due ON invoices(status, due_date);
CREATE INDEX idx_maintenance_status ON maintenance_requests(status);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
