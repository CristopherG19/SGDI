"""
Script para crear las tablas directamente en MySQL
"""
import mysql.connector

mysql_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'sgdi',
    'charset': 'utf8mb4'
}

schema_sql = """
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

CREATE TABLE IF NOT EXISTS qr_operations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(500),
    qr_content TEXT,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    items_processed INT DEFAULT 0,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (operation_type),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS file_audits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folder_path VARCHAR(500) NOT NULL,
    total_expected INT NOT NULL,
    total_found INT NOT NULL,
    missing_count INT NOT NULL,
    extra_count INT NOT NULL,
    report_path VARCHAR(500),
    audit_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at),
    INDEX idx_folder (folder_path(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_name VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    traceback TEXT,
    extra_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level (level),
    INDEX idx_module (module_name),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

try:
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    
    print("🔧 Creando tablas en MySQL...")
    
    for statement in schema_sql.split(';'):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)
            print("✓ Tabla creada")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Todas las tablas creadas exitosamente")
    
except mysql.connector.Error as e:
    print(f"❌ Error: {e}")
