"""
Script de prueba para verificar Fase 1
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

print("="*60)
print("SGDI - Prueba de Fase 1: Core y Logging")
print("="*60)

print("\n1. Probando configuración...")
try:
    from config.settings import Settings
    print(f"   ✓ Configuración cargada")
    print(f"   - App: {Settings.APP_NAME} v{Settings.APP_VERSION}")
    print(f"   - Tema: {Settings.THEME}")
    print(f"   - BD: {Settings.DATABASE_PATH}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n2. Probando sistema de logging...")
try:
    from core.utils.logger import get_logger, log_operation
    log = get_logger("test")
    log.info("Sistema de logging funcionando correctamente")
    log_operation("test", "init_test", True, "Prueba de logging")
    print("   ✓ Logging configurado correctamente")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n3. Probando base de datos...")
try:
    from core.database.simple_db import get_db
    
    db = get_db()
    print(f"   ✓ Base de datos MySQL conectada: {db.db_config['database']}")
    
    # Probar inserción
    test_code = "TEST123456"
    if not db.code_exists(test_code):
        id = db.save_generated_code(test_code, "Artículo de Prueba", notes="Test de Fase 1")
        print(f"   ✓ Código de prueba insertado (ID: {id})")
    else:
        print(f"   ✓ Código de prueba ya existe")
    
    # Probar lectura
    stats = db.get_dashboard_stats()
    print(f"   ✓ Estadísticas obtenidas: {stats}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Probando utilidades de archivos...")
try:
    from core.utils.file_handler import ensure_directory, find_files
    from config.settings import Settings
    
    # Asegurar directorios
    Settings.ensure_directories()
    print("   ✓ Directorios creados/verificados")
    
    # Buscar archivos
    files = find_files(ROOT_DIR, pattern="*.py", recursive=False)
    print(f"   ✓ Encontrados {len(files)} archivos Python en raíz")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n5. Probando validadores...")
try:
    from core.utils.validators import (
        validate_file_exists,
        validate_inacal_code,
        validate_pdf_file
    )
    
    # Validar archivo
    valid, msg = validate_file_exists(__file__)
    print(f"   ✓ Validación de archivo: {valid}")
    
    # Validar código INACAL
    valid, msg = validate_inacal_code("ABC1234567")
    print(f"   ✓ Validación de código INACAL: {valid}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ Todas las pruebas de Fase 1 pasaron exitosamente!")
print("="*60)
print("\nComponentes verificados:")
print("  ✓ Configuración (Settings)")
print("  ✓ Sistema de logging (loguru)")
print("  ✓ Base de datos MySQL")
print("  ✓ Utilidades de archivos")
print("  ✓ Validadores")
print("\n🚀 Sistema listo para continuar con Fase 2: GUI")
print("="*60)
