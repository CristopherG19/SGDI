"""
Script para inspeccionar los datos actuales en SQLite
antes de la migración a MySQL
"""

import sqlite3
from pathlib import Path

# Ruta a la base de datos SQLite
DB_PATH = Path(__file__).parent / "data" / "database" / "sgdi.db"

def inspect_database():
    """Inspecciona la base de datos SQLite y muestra estadísticas."""
    
    if not DB_PATH.exists():
        print(f"❌ Base de datos no encontrada: {DB_PATH}")
        return
    
    print(f"📊 Inspeccionando base de datos: {DB_PATH}")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obtener lista de tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📋 Tablas encontradas: {len(tables)}")
    print("-" * 70)
    
    total_records = 0
    
    for table in tables:
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_records += count
        
        # Obtener columnas
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📁 {table}")
        print(f"   Registros: {count}")
        print(f"   Columnas: {', '.join(columns)}")
        
        # Mostrar algunos datos de ejemplo si hay registros
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            rows = cursor.fetchall()
            print(f"   Primeros {len(rows)} registros:")
            for i, row in enumerate(rows, 1):
                print(f"     {i}. {dict(zip(columns, row))}")
    
    print("\n" + "=" * 70)
    print(f"✅ Total de registros en toda la BD: {total_records}")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()
