-- UrbanPulse Seed Data — Antalya Edition
-- Runs on startup only when spring.sql.init.mode=always (dev profile)
-- INSERT IGNORE is idempotent — safe to run multiple times on MySQL

-- Departments (Antalya Büyükşehir Belediyesi)
INSERT IGNORE INTO departments (id, name, type, capacity, current_load, contact_email) VALUES
(1, 'Antalya Trafik Yönetim Müdürlüğü',  'TRAFFIC',        15, 6, 'trafik@antalya.bel.tr'),
(2, 'Antalya Yollar ve Altyapı Dairesi',  'INFRASTRUCTURE', 12, 4, 'altyapi@antalya.bel.tr'),
(3, 'Antalya Çevre Sağlığı Müdürlüğü',   'ENVIRONMENT',    10, 3, 'cevre@antalya.bel.tr'),
(4, 'AEDAŞ (Antalya Elektrik Dağıtım)',   'ENERGY',          8, 5, 'aedas@antalya.bel.tr'),
(5, 'Antalya Zabıta ve Güvenlik Müd.',    'SAFETY',         20, 8, 'zabita@antalya.bel.tr'),
(6, 'ASAT (Antalya Su ve Atıksu İd.)',    'HEALTH',         10, 2, 'asat@antalya.bel.tr');

-- Update existing department emails if rows already exist
UPDATE departments SET contact_email = 'trafik@antalya.bel.tr',  name = 'Antalya Trafik Yönetim Müdürlüğü' WHERE id = 1;
UPDATE departments SET contact_email = 'altyapi@antalya.bel.tr', name = 'Antalya Yollar ve Altyapı Dairesi'  WHERE id = 2;
UPDATE departments SET contact_email = 'cevre@antalya.bel.tr',   name = 'Antalya Çevre Sağlığı Müdürlüğü'   WHERE id = 3;
UPDATE departments SET contact_email = 'aedas@antalya.bel.tr',   name = 'AEDAŞ (Antalya Elektrik Dağıtım)'   WHERE id = 4;
UPDATE departments SET contact_email = 'zabita@antalya.bel.tr',  name = 'Antalya Zabıta ve Güvenlik Müd.'    WHERE id = 5;
UPDATE departments SET contact_email = 'asat@antalya.bel.tr',    name = 'ASAT (Antalya Su ve Atıksu İd.)'    WHERE id = 6;

-- Users (password for all: test123)
-- Hash generated with BCryptPasswordEncoder(strength=10)
INSERT IGNORE INTO users (id, name, email, password_hash, role, district, enabled, created_at) VALUES
(1, 'Admin User',    'admin@urbanpulse.com',
 '$2a$10$uWB8xbSSatfJTs7qEI17yeZYB7vo8/C3g2daH.FMivRcIRqi.TCeu',
 'ADMIN', 'Muratpaşa', true, NOW()),
(2, 'Staff Member',  'staff@urbanpulse.com',
 '$2a$10$uWB8xbSSatfJTs7qEI17yeZYB7vo8/C3g2daH.FMivRcIRqi.TCeu',
 'STAFF', 'Konyaaltı', true, NOW()),
(3, 'Ahmet Yılmaz', 'ahmet@example.com',
 '$2a$10$uWB8xbSSatfJTs7qEI17yeZYB7vo8/C3g2daH.FMivRcIRqi.TCeu',
 'CITIZEN', 'Muratpaşa', true, NOW());

-- Update existing user districts if rows already exist (INSERT IGNORE won't update)
UPDATE users SET district = 'Muratpaşa' WHERE id = 1;
UPDATE users SET district = 'Konyaaltı' WHERE id = 2;
UPDATE users SET district = 'Muratpaşa' WHERE id = 3;
