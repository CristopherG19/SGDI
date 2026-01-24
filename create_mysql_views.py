"""
Script para crear las vistas en MySQL
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

views_sql = [
    """
    CREATE OR REPLACE VIEW v_dashboard_stats AS
    SELECT
        (SELECT COUNT(*) FROM generated_codes) as total_codes_generated,
        (SELECT COUNT(*) FROM qr_operations WHERE DATE(created_at) = CURDATE()) as qr_operations_today,
        (SELECT COUNT(*) FROM file_audits WHERE DATE(created_at) = CURDATE()) as audits_today,
        (SELECT COALESCE(SUM(space_saved_mb), 0) FROM pdf_compressions) as total_space_saved_mb,
        (SELECT COUNT(*) FROM file_searches WHERE DATE(created_at) = CURDATE()) as searches_today
    """,
    """
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
    LIMIT 100
    """
]

try:
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    
    print("🔧 Creando vistas en MySQL...")
    
    for view_sql in views_sql:
        cursor.execute(view_sql)
        print("✓ Vista creada")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Todas las vistas creadas exitosamente")
    
except mysql.connector.Error as e:
    print(f"❌ Error: {e}")
