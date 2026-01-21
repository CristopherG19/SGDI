-- ===================================
-- SGDI - Esquema de Base de Datos
-- ===================================
-- Sistema de Gestión Documental Integral
-- SQLite Database Schema
-- Versión: 1.0.0
-- Fecha: 2026-01-21
-- ===================================

-- Tabla de Códigos Generados (INACAL)
-- Almacena todos los códigos únicos generados
CREATE TABLE IF NOT EXISTS generated_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    article_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported_to_excel BOOLEAN DEFAULT 0,
    excel_export_path VARCHAR(500),
    notes TEXT
);

-- Tabla de Operaciones QR
-- Registra todas las operaciones realizadas con códigos QR
CREATE TABLE IF NOT EXISTS qr_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type VARCHAR(20) NOT NULL,  -- 'generate', 'read', 'rename', 'process_excel'
    file_path VARCHAR(500),
    qr_content TEXT,
    status VARCHAR(20) NOT NULL,  -- 'success', 'error', 'warning'
    error_message TEXT,
    items_processed INTEGER DEFAULT 0,
    duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Auditorías de Archivos
-- Registra los resultados de auditorías de archivos
CREATE TABLE IF NOT EXISTS file_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path VARCHAR(500) NOT NULL,
    total_expected INTEGER NOT NULL,
    total_found INTEGER NOT NULL,
    missing_count INTEGER NOT NULL,
    extra_count INTEGER NOT NULL,
    report_path VARCHAR(500),
    audit_type VARCHAR(50),  -- 'inacal', 'general', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Compresiones PDF
-- Registra las operaciones de compresión de PDFs
CREATE TABLE IF NOT EXISTS pdf_compressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path VARCHAR(500) NOT NULL,
    files_processed INTEGER NOT NULL,
    files_skipped INTEGER DEFAULT 0,
    files_error INTEGER DEFAULT 0,
    original_size_mb REAL NOT NULL,
    compressed_size_mb REAL NOT NULL,
    space_saved_mb REAL NOT NULL,
    compression_ratio REAL,
    compression_quality INTEGER DEFAULT 70,
    duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Búsquedas de Archivos
-- Registra las operaciones de búsqueda y copia de archivos
CREATE TABLE IF NOT EXISTS file_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path VARCHAR(500) NOT NULL,
    destination_path VARCHAR(500) NOT NULL,
    files_searched INTEGER NOT NULL,
    files_found INTEGER NOT NULL,
    files_copied INTEGER NOT NULL,
    files_error INTEGER DEFAULT 0,
    search_pattern TEXT,
    duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Logs del Sistema
-- Almacena logs importantes del sistema
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    level VARCHAR(10) NOT NULL,  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message TEXT NOT NULL,
    traceback TEXT,
    extra_data TEXT,  -- JSON string con datos adicionales
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- ÍNDICES
-- ===================================

-- Índices para optimización de consultas
CREATE INDEX IF NOT EXISTS idx_generated_codes_code ON generated_codes(code);
CREATE INDEX IF NOT EXISTS idx_generated_codes_created ON generated_codes(created_at);

CREATE INDEX IF NOT EXISTS idx_qr_operations_type ON qr_operations(operation_type);
CREATE INDEX IF NOT EXISTS idx_qr_operations_status ON qr_operations(status);
CREATE INDEX IF NOT EXISTS idx_qr_operations_created ON qr_operations(created_at);

CREATE INDEX IF NOT EXISTS idx_file_audits_created ON file_audits(created_at);
CREATE INDEX IF NOT EXISTS idx_file_audits_folder ON file_audits(folder_path);

CREATE INDEX IF NOT EXISTS idx_pdf_compressions_created ON pdf_compressions(created_at);
CREATE INDEX IF NOT EXISTS idx_pdf_compressions_folder ON pdf_compressions(folder_path);

CREATE INDEX IF NOT EXISTS idx_file_searches_created ON file_searches(created_at);

CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_created ON system_logs(created_at);

-- ===================================
-- VISTAS (opcional)
-- ===================================

-- Vista para estadísticas generales
CREATE VIEW IF NOT EXISTS v_dashboard_stats AS
SELECT
    (SELECT COUNT(*) FROM generated_codes) as total_codes_generated,
    (SELECT COUNT(*) FROM qr_operations WHERE DATE(created_at) = DATE('now')) as qr_operations_today,
    (SELECT COUNT(*) FROM file_audits WHERE DATE(created_at) = DATE('now')) as audits_today,
    (SELECT COALESCE(SUM(space_saved_mb), 0) FROM pdf_compressions) as total_space_saved_mb,
    (SELECT COUNT(*) FROM file_searches WHERE DATE(created_at) = DATE('now')) as searches_today;

-- Vista para logs recientes
CREATE VIEW IF NOT EXISTS v_recent_logs AS
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
-- TRIGGERS (opcional)
-- ===================================

-- Trigger para limpiar logs antiguos automáticamente
-- (Mantener solo los últimos 10,000 registros)
CREATE TRIGGER IF NOT EXISTS trg_cleanup_old_logs
AFTER INSERT ON system_logs
WHEN (SELECT COUNT(*) FROM system_logs) > 10000
BEGIN
    DELETE FROM system_logs 
    WHERE id IN (
        SELECT id FROM system_logs 
        ORDER BY created_at ASC 
        LIMIT (SELECT COUNT(*) - 10000 FROM system_logs)
    );
END;

-- ===================================
-- DATOS INICIALES (opcional)
-- ===================================

-- Insertar log de inicialización
INSERT OR IGNORE INTO system_logs (module_name, action, level, message)
VALUES ('database', 'schema_initialization', 'INFO', 'Base de datos inicializada correctamente');
