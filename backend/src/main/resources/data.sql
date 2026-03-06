-- UrbanPulse Seed Data
-- Runs on startup only when spring.sql.init.mode=always (dev profile)
-- INSERT IGNORE is idempotent — safe to run multiple times on MySQL

-- Departments
INSERT IGNORE INTO departments (id, name, type, capacity, current_load, contact_email) VALUES
(1, 'Traffic Department',        'TRAFFIC',        15, 6, 'traffic@istanbul.gov.tr'),
(2, 'Infrastructure Department', 'INFRASTRUCTURE', 12, 4, 'infra@istanbul.gov.tr'),
(3, 'Environmental Department',  'ENVIRONMENT',    10, 3, 'environment@istanbul.gov.tr'),
(4, 'Energy Department',         'ENERGY',          8, 5, 'energy@istanbul.gov.tr'),
(5, 'Public Safety Department',  'SAFETY',         20, 8, 'safety@istanbul.gov.tr'),
(6, 'Environmental Health',      'HEALTH',         10, 2, 'health@istanbul.gov.tr');

-- Users (password for all: test123)
-- Hash generated with BCryptPasswordEncoder(strength=10)
INSERT IGNORE INTO users (id, name, email, password_hash, role, district, enabled, created_at) VALUES
(1, 'Admin User',    'admin@urbanpulse.com',
 '$2a$10$uWB8xbSSatfJTs7qEI17yeZYB7vo8/C3g2daH.FMivRcIRqi.TCeu',
 'ADMIN', 'Şişli', true, NOW()),
(2, 'Staff Member',  'staff@urbanpulse.com',
 '$2a$10$uWB8xbSSatfJTs7qEI17yeZYB7vo8/C3g2daH.FMivRcIRqi.TCeu',
 'STAFF', 'Kadıköy', true, NOW()),
(3, 'Ahmet Yılmaz', 'ahmet@example.com',
 '$2a$10$uWB8xbSSatfJTs7qEI17yeZYB7vo8/C3g2daH.FMivRcIRqi.TCeu',
 'CITIZEN', 'Kadıköy', true, NOW());
