-- ===================================
-- SGDI - Esquema de Base de Datos MySQL
-- ===================================
-- Sistema de Gestión Documental Integral
-- MySQL Database Schema
-- Versión: 1.0.0
-- Fecha: 2026-01-23
-- ===================================

-- Tabla de Códigos Generados (INACAL)
-- Almacena todos los códigos únicos generados
CREATE TABLE IF NOT EXISTS generated_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    article_name VARCHAR(100) NOT NULL,
    meter_serial VARCHAR(100) DEFAULT '',
    service_type VARCHAR(100) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported_to_excel TINYINT(1) DEFAULT 0,
    excel_export_path VARCHAR(500),
    notes TEXT,
    INDEX idx_code (code),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de Operaciones QR
-- Registra todas las operaciones realizadas con códigos QR
CREATE TABLE IF NOT EXISTS qr_operations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_type VARCHAR(20) NOT NULL,  -- 'generate', 'read', 'rename', 'process_excel'
    file_path VARCHAR(500),
    qr_content TEXT,
    status VARCHAR(20) NOT NULL,  -- 'success', 'error', 'warning'
    error_message TEXT,
    items_processed INT DEFAULT 0,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (operation_type),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de Auditorías de Archivos
-- Registra los resultados de auditorías de archivos
CREATE TABLE IF NOT EXISTS file_audits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folder_path VARCHAR(500) NOT NULL,
    total_expected INT NOT NULL,
    total_found INT NOT NULL,
    missing_count INT NOT NULL,
    extra_count INT NOT NULL,
    report_path VARCHAR(500),
    audit_type VARCHAR(50),  -- 'inacal', 'general', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at),
    INDEX idx_folder (folder_path(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de Compresiones PDF
-- Registra las operaciones de compresión de PDFs
CREATE TABLE IF NOT EXISTS pdf_compressions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folder_path VARCHAR(500) NOT NULL,
    files_processed INT NOT NULL,
    files_skipped INT DEFAULT 0,
    files_error INT DEFAULT 0,
    original_size_mb DECIMAL(10,2) NOT NULL,
    compressed_size_mb DECIMAL(10,2) NOT NULL,
    space_saved_mb DECIMAL(10,2) NOT NULL,
    compression_ratio DECIMAL(5,2),
    compression_quality INT DEFAULT 70,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at),
    INDEX idx_folder (folder_path(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de Búsquedas de Archivos
-- Registra las operaciones de búsqueda y copia de archivos
CREATE TABLE IF NOT EXISTS file_searches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_path VARCHAR(500) NOT NULL,
    destination_path VARCHAR(500) NOT NULL,
    files_searched INT NOT NULL,
    files_found INT NOT NULL,
    files_copied INT NOT NULL,
    files_error INT DEFAULT 0,
    search_pattern TEXT,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de Logs del Sistema
-- Almacena logs importantes del sistema
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_name VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    level VARCHAR(10) NOT NULL,  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message TEXT NOT NULL,
    traceback TEXT,
    extra_data TEXT,  -- JSON string con datos adicionales
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level (level),
    INDEX idx_module (module_name),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================================
-- VISTAS
-- ===================================

-- Vista para estadísticas generales
CREATE OR REPLACE VIEW v_dashboard_stats AS
SELECT
    (SELECT COUNT(*) FROM generated_codes) as total_codes_generated,
    (SELECT COUNT(*) FROM qr_operations WHERE DATE(created_at) = CURDATE()) as qr_operations_today,
    (SELECT COUNT(*) FROM file_audits WHERE DATE(created_at) = CURDATE()) as audits_today,
    (SELECT COALESCE(SUM(space_saved_mb), 0) FROM pdf_compressions) as total_space_saved_mb,
    (SELECT COUNT(*) FROM file_searches WHERE DATE(created_at) = CURDATE()) as searches_today;

-- Vista para logs recientes
CREATE OR REPLACE VIEW v_recent_logs AS
SELECT 
    id,
    module_name,
    action,
    level,
    message,
    created_at
FROM system_logs
ORDER BY created_at DESC
LIMIT 100;

-- ===================================
-- DATOS INICIALES
-- ===================================

-- Insertar log de inicialización
INSERT INTO system_logs (module_name, action, level, message)
VALUES ('database', 'schema_initialization', 'INFO', 'Base de datos MySQL inicializada correctamente')
ON DUPLICATE KEY UPDATE module_name=module_name;
