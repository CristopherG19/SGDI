from core.database.simple_db import get_db

db = get_db()

# SQL para crear tabla
sql = """
CREATE TABLE IF NOT EXISTS dropbox_urls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_path VARCHAR(768) UNIQUE NOT NULL,
    file_name VARCHAR(500) NOT NULL,
    folder_type VARCHAR(50),
    shared_url VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    modified_date DATETIME,
    extraction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    INDEX idx_folder_type (folder_type),
    INDEX idx_extraction_date (extraction_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

try:
    db.cursor.execute(sql)
    db.conn.commit()
    print("✅ Tabla dropbox_urls creada exitosamente")
except Exception as e:
    print(f"❌ Error: {e}")
