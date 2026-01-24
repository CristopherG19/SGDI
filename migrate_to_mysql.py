"""
Script de Migración: SQLite → MySQL
====================================
Migra todos los datos desde la base de datos SQLite actual a MySQL.
Preserva todos los registros existentes.
"""

import sqlite3
import mysql.connector
from pathlib import Path
from typing import Dict, List, Any
import sys

# Configuración
SQLITE_DB_PATH = Path(__file__).parent / "data" / "database" / "sgdi.db"
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}
MYSQL_DB_NAME = 'sgdi'

# Tablas a migrar (en orden)
TABLES = [
    'generated_codes',
    'qr_operations',
    'file_audits',
    'pdf_compressions',
    'file_searches',
    'system_logs'
]


def create_mysql_database():
    """Crea la base de datos MySQL si no existe."""
    print("\n📊 Paso 1: Creando base de datos MySQL...")
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Crear base de datos
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Base de datos '{MYSQL_DB_NAME}' creada/verificada")
        
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"❌ Error al crear base de datos: {e}")
        return False


def execute_mysql_schema():
    """Ejecuta el schema de MySQL."""
    print("\n📋 Paso 2: Ejecutando schema de MySQL...")
    
    schema_path = Path(__file__).parent / "core" / "database" / "schema_mysql.sql"
    
    if not schema_path.exists():
        print(f"❌ Schema no encontrado: {schema_path}")
        return False
    
    try:
        # Conectar a la base de datos
        config = MYSQL_CONFIG.copy()
        config['database'] = MYSQL_DB_NAME
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Leer y ejecutar schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Ejecutar cada statement
        for statement in schema_sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as e:
                    # Ignorar errores de "ya existe"
                    if "already exists" not in str(e).lower() and "Duplicate entry" not in str(e):
                        print(f"⚠️ Advertencia: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Schema ejecutado correctamente")
        return True
    except mysql.connector.Error as e:
        print(f"❌ Error al ejecutar schema: {e}")
        return False


def migrate_table_data(table_name: str, sqlite_conn, mysql_conn):
    """Migra los datos de una tabla específica."""
    
    # Leer datos de SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"   ⚪ {table_name}: 0 registros (tabla vacía)")
        return 0
    
    # Obtener nombres de columnas
    column_names = [description[0] for description in sqlite_cursor.description]
    
    # Preparar INSERT para MySQL
    placeholders = ', '.join(['%s' for _ in column_names])
    columns_str = ', '.join(column_names)
    insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    # Insertar en MySQL
    mysql_cursor = mysql_conn.cursor()
    migrated_count = 0
    error_count = 0
    
    for row in rows:
        try:
            mysql_cursor.execute(insert_query, row)
            migrated_count += 1
        except mysql.connector.Error as e:
            # Ignorar duplicados
            if "Duplicate entry" not in str(e):
                error_count += 1
                if error_count <= 3:  # Mostrar solo los primeros 3 errores
                    print(f"      ⚠️ Error en registro: {e}")
    
    mysql_conn.commit()
    
    if migrated_count > 0:
        print(f"   ✓ {table_name}: {migrated_count:,} registros migrados", end="")
        if error_count > 0:
            print(f" ({error_count} errores)")
        else:
            print()
    
    return migrated_count


def migrate_all_data():
    """Migra todos los datos de SQLite a MySQL."""
    print("\n📦 Paso 3: Migrando datos...")
    
    if not SQLITE_DB_PATH.exists():
        print(f"❌ Base de datos SQLite no encontrada: {SQLITE_DB_PATH}")
        return False
    
    try:
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        
        # Conectar a MySQL
        mysql_config = MYSQL_CONFIG.copy()
        mysql_config['database'] = MYSQL_DB_NAME
        mysql_conn = mysql.connector.connect(**mysql_config)
        
        total_migrated = 0
        
        # Migrar cada tabla
        for table in TABLES:
            count = migrate_table_data(table, sqlite_conn, mysql_conn)
            total_migrated += count
        
        # Cerrar conexiones
        sqlite_conn.close()
        mysql_conn.close()
        
        print(f"\n✅ Migración completada: {total_migrated:,} registros totales")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False


def verify_migration():
    """Verifica que los datos se migraron correctamente."""
    print("\n🔍 Paso 4: Verificando migración...")
    
    try:
        # Conectar a ambas bases de datos
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        mysql_config = MYSQL_CONFIG.copy()
        mysql_config['database'] = MYSQL_DB_NAME
        mysql_conn = mysql.connector.connect(**mysql_config)
        mysql_cursor = mysql_conn.cursor()
        
        all_match = True
        
        for table in TABLES:
            # Contar en SQLite
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            # Contar en MySQL
            mysql_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            mysql_count = mysql_cursor.fetchone()[0]
            
            if sqlite_count == mysql_count:
                if sqlite_count > 0:
                    print(f"   ✓ {table}: {sqlite_count:,} registros ✓")
            else:
                print(f"   ⚠️ {table}: SQLite={sqlite_count:,}, MySQL={mysql_count:,}")
                all_match = False
        
        sqlite_conn.close()
        mysql_conn.close()
        
        if all_match:
            print("\n✅ Verificación exitosa: Todos los datos coinciden")
        else:
            print("\n⚠️ Advertencia: Algunos conteos no coinciden")
        
        return all_match
        
    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        return False


def main():
    """Función principal de migración."""
    print("=" * 70)
    print("🔄 MIGRACIÓN DE BASE DE DATOS: SQLite → MySQL")
    print("=" * 70)
    
    # Verificar que SQLite existe
    if not SQLITE_DB_PATH.exists():
        print(f"\n❌ Base de datos SQLite no encontrada: {SQLITE_DB_PATH}")
        print("   No hay datos para migrar.")
        sys.exit(1)
    
    print(f"\n📍 Origen:  {SQLITE_DB_PATH}")
    print(f"📍 Destino: MySQL ({MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_DB_NAME})")
    
    # Paso 1: Crear base de datos
    if not create_mysql_database():
        print("\n❌ Migración abortada")
        sys.exit(1)
    
    # Paso 2: Ejecutar schema
    if not execute_mysql_schema():
        print("\n❌ Migración abortada")
        sys.exit(1)
    
    # Paso 3: Migrar datos
    if not migrate_all_data():
        print("\n❌ Migración abortada")
        sys.exit(1)
    
    # Paso 4: Verificar
    verify_migration()
    
    print("\n" + "=" * 70)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print("\n💡 Próximos pasos:")
    print("   1. Verifica que el sistema funcione correctamente")
    print("   2. Puedes usar MySQL Workbench o phpMyAdmin para explorar la BD")
    print("   3. El archivo SQLite original se mantiene como respaldo")
    print()


if __name__ == "__main__":
    main()
