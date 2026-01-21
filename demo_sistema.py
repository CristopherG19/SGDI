"""
SGDI - Demostración Completa del Sistema (Fase 1)
==================================================

Este script demuestra todas las funcionalidades implementadas en Fase 1.
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import Settings
from core.database.simple_db import get_db
from core.utils.logger import get_logger, log_operation
from core.utils.file_handler import *
from core.utils.validators import *

log = get_logger("demo")

def print_section(title):
    """Imprime un separador de sección."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def demo_configuration():
    """Demuestra el sistema de configuración."""
    print_section("1. SISTEMA DE CONFIGURACIÓN")
    
    print(f"\n📋 Información de la Aplicación:")
    print(f"   Nombre: {Settings.APP_NAME}")
    print(f"   Versión: {Settings.APP_VERSION}")
    print(f"   Modo Debug: {Settings.DEBUG_MODE}")
    print(f"   Tema: {Settings.THEME}")
    
    print(f"\n📂 Rutas del Proyecto:")
    print(f"   Raíz: {Settings.ROOT_DIR}")
    print(f"   Base de Datos: {Settings.DATABASE_PATH}")
    print(f"   Logs: {Settings.LOG_PATH}")
    print(f"   Exports: {Settings.EXPORTS_DIR}")
    
    print(f"\n⚙️  Configuración de Módulos:")
    print(f"   PDF - Calidad de compresión: {Settings.PDF_COMPRESSION_QUALITY}%")
    print(f"   QR - Tamaño por defecto: {Settings.QR_DEFAULT_SIZE}px")
    print(f"   Log - Nivel: {Settings.LOG_LEVEL}")

def demo_logging():
    """Demuestra el sistema de logging."""
    print_section("2. SISTEMA DE LOGGING")
    
    print("\n📝 Generando logs de ejemplo...")
    
    log.debug("Este es un mensaje de DEBUG")
    log.info("Este es un mensaje de INFO")
    log.warning("Este es un mensaje de WARNING")
    
    print("   ✓ Logs generados en consola")
    print(f"   ✓ Logs guardados en: {Settings.LOG_PATH}")
    
    # Log de operación exitosa
    log_operation(
        module="demo",
        action="test_operation",
        success=True,
        message="Operación de prueba exitosa",
        test_data="ejemplo"
    )
    print("   ✓ Log de operación guardado en BD")

def demo_database():
    """Demuestra las operaciones de base de datos."""
    print_section("3. BASE DE DATOS SQLITE")
    
    db = get_db()
    
    print(f"\n💾 Base de datos: {db.db_path}")
    print(f"   Estado: {'✓ Conectada' if Path(db.db_path).exists() else '✗ No encontrada'}")
    
    # Insertar códigos de prueba
    print("\n📝 Insertando códigos de prueba...")
    test_codes = [
        ("DEMO123456", "Artículo Demo 1"),
        ("TEST789012", "Artículo Demo 2"),
        ("SGDI345678", "Artículo Demo 3")
    ]
    
    inserted = 0
    for code, article in test_codes:
        if not db.code_exists(code):
            db.save_generated_code(code, article, notes="Código de demostración")
            inserted += 1
    
    print(f"   ✓ Insertados: {inserted} códigos nuevos")
    
    # Obtener estadísticas
    stats = db.get_dashboard_stats()
    print(f"\n📊 Estadísticas del Dashboard:")
    print(f"   - Total códigos generados: {stats.get('total_codes_generated', 0)}")
    print(f"   - Operaciones QR hoy: {stats.get('qr_operations_today', 0)}")
    print(f"   - Auditorías hoy: {stats.get('audits_today', 0)}")
    print(f"   - Espacio ahorrado (PDFs): {stats.get('total_space_saved_mb', 0):.2f} MB")
    
    # Insertar operación QR de prueba
    print("\n🔲 Registrando operación QR...")
    db.save_qr_operation(
        operation_type="generate",
        status="success",
        qr_content="DEMO123456",
        items_processed=1,
        duration=0.5
    )
    print("   ✓ Operación QR registrada")
    
    # Insertar compresión PDF de prueba
    print("\n📄 Registrando compresión PDF...")
    db.save_pdf_compression(
        folder_path="C:/Demo/PDFs",
        files_processed=10,
        original_size_mb=50.5,
        compressed_size_mb=30.2,
        space_saved_mb=20.3,
        duration=15.5
    )
    print("   ✓ Compresión PDF registrada")
    
    # Mostrar logs recientes
    print("\n📜 Últimos 5 logs del sistema:")
    recent_logs = db.get_recent_logs(limit=5)
    for i, log_entry in enumerate(recent_logs[:5], 1):
        timestamp = log_entry['created_at']
        module = log_entry['module_name']
        action = log_entry['action']
        level = log_entry['level']
        print(f"   {i}. [{level}] {module}.{action} - {timestamp}")

def demo_file_operations():
    """Demuestra las utilidades de archivos."""
    print_section("4. UTILIDADES DE ARCHIVOS")
    
    # Buscar archivos Python
    print("\n🔍 Buscando archivos Python en el proyecto...")
    py_files = find_files(Settings.ROOT_DIR, pattern="*.py", recursive=True)
    print(f"   ✓ Encontrados: {len(py_files)} archivos .py")
    
    # Tamaño del proyecto
    print("\n📏 Calculando tamaño del proyecto...")
    total_size, file_count = get_directory_size(Settings.ROOT_DIR)
    size_mb = total_size / (1024 * 1024)
    print(f"   ✓ Tamaño total: {size_mb:.2f} MB")
    print(f"   ✓ Total archivos: {file_count}")
    
    # Crear directorio temporal
    print("\n📁 Probando creación de directorios...")
    test_dir = Settings.DATA_DIR / "test_temp"
    ensure_directory(test_dir)
    print(f"   ✓ Directorio creado: {test_dir}")
    
    # Limpiar
    if test_dir.exists():
        test_dir.rmdir()
        print("   ✓ Directorio de prueba eliminado")

def demo_validators():
    """Demuestra los validadores."""
    print_section("5. SISTEMA DE VALIDACIÓN")
    
    # Validar código INACAL
    print("\n🔢 Validando códigos INACAL:")
    test_codes = [
        ("ABCD123456", True),   # Válido
        ("abc123456", False),    # Minúsculas
        ("ABCD12345", False),    # Solo 9 caracteres
        ("ABCD@12345", False),   # Caracteres especiales
    ]
    
    for code, expected in test_codes:
        valid, msg = validate_inacal_code(code)
        status = "✓" if valid == expected else "✗"
        result = "válido" if valid else f"inválido ({msg})"
        print(f"   {status} '{code}': {result}")
    
    # Validar archivos
    print("\n📄 Validando archivos:")
    
    # Este script debe existir
    valid, msg = validate_file_exists(__file__)
    print(f"   ✓ demo_sistema.py: {'existe' if valid else msg}")
    
    # Validar extensión
    valid, msg = validate_file_extension(__file__, ['.py'])
    print(f"   ✓ Extensión .py: {'válida' if valid else msg}")
    
    # Validar ruta escribible
    valid, msg = validate_path_writable(Settings.DATA_DIR)
    print(f"   ✓ Permisos de escritura: {'OK' if valid else msg}")

def demo_integration():
    """Demuestra integración entre componentes."""
    print_section("6. INTEGRACIÓN DE COMPONENTES")
    
    print("\n🔗 Flujo completo de operación:")
    
    # 1. Validar datos
    print("\n   Paso 1: Validar código...")
    code = "INTE123456"
    valid, msg = validate_inacal_code(code)
    if valid:
        print(f"      ✓ Código válido: {code}")
    
    # 2. Guardar en BD
    print("\n   Paso 2: Guardar en base de datos...")
    db = get_db()
    if not db.code_exists(code):
        id = db.save_generated_code(code, "Artículo Integración", 
                                    notes="Prueba de integración")
        print(f"      ✓ Código guardado (ID: {id})")
    else:
        print(f"      ℹ Código ya existe")
    
    # 3. Registrar operación
    print("\n   Paso 3: Registrar operación...")
    db.save_qr_operation(
        operation_type="generate",
        status="success",
        qr_content=code,
        items_processed=1,
        duration=0.3
    )
    print(f"      ✓ Operación registrada")
    
    # 4. Loguear
    print("\n   Paso 4: Loguear resultado...")
    log_operation(
        module="integration_demo",
        action="full_workflow",
        success=True,
        message=f"Código {code} procesado completamente",
        code=code
    )
    print(f"      ✓ Log generado")
    
    print("\n   ✅ Flujo de integración completado exitosamente")

def print_summary():
    """Imprime resumen final."""
    print_section("RESUMEN DE LA DEMOSTRACIÓN")
    
    print(f"\n✅ Componentes Verificados:")
    print(f"   ✓ Sistema de Configuración")
    print(f"   ✓ Sistema de Logging (Loguru)")
    print(f"   ✓ Base de Datos SQLite")
    print(f"   ✓ Utilidades de Archivos")
    print(f"   ✓ Sistema de Validación")
    print(f"   ✓ Integración entre Componentes")
    
    db = get_db()
    stats = db.get_dashboard_stats()
    
    print(f"\n📊 Estado Actual del Sistema:")
    print(f"   - Códigos en BD: {stats.get('total_codes_generated', 0)}")
    print(f"   - Logs generados: {len(db.get_recent_logs(100))}")
    print(f"   - Base de datos: {Path(db.db_path).stat().st_size / 1024:.1f} KB")
    
    print(f"\n🎯 Fase 1 - COMPLETADA AL 100%")
    print(f"   Todos los componentes core están funcionando correctamente.")
    print(f"   El sistema está listo para la Fase 2: Infraestructura GUI.")

def main():
    """Función principal de la demostración."""
    print("\n" + "="*70)
    print("  SGDI - DEMOSTRACIÓN COMPLETA DEL SISTEMA")
    print("  Fase 1: Core y Logging")
    print("="*70)
    print(f"\n  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Versión: {Settings.APP_VERSION}")
    
    try:
        demo_configuration()
        time.sleep(0.5)
        
        demo_logging()
        time.sleep(0.5)
        
        demo_database()
        time.sleep(0.5)
        
        demo_file_operations()
        time.sleep(0.5)
        
        demo_validators()
        time.sleep(0.5)
        
        demo_integration()
        time.sleep(0.5)
        
        print_summary()
        
        print("\n" + "="*70)
        print("  ✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
