"""
SGDI - Script de Migración de Códigos INACAL
=============================================

Migra los códigos existentes desde el archivo TXT a la base de datos SQLite.
"""

import os
import sys
from pathlib import Path

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from core.database.simple_db import get_db
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


def migrate_inacal_codes():
    """
    Migra los códigos INACAL desde el archivo TXT a la base de datos.
    
    Returns:
        Tupla (códigos_migrados, códigos_duplicados, errores)
    """
    log.info("="*60)
    log.info("Iniciando migración de códigos INACAL")
    log.info("="*60)
    
    inacal_file = Settings.INACAL_CODES_PATH
   log.info(f"Archivo fuente: {inacal_file}")
    
    # Verificar que el archivo existe
    if not os.path.exists(inacal_file):
        log.warning(f"Archivo INACAL no encontrado: {inacal_file}")
        log.info("Se omite la migración. El sistema funcionará sin códigos históricos.")
        return 0, 0, 0
    
    # Conectar a la base de datos
    db = get_db()
    
    migrated = 0
    duplicates = 0
    errors = 0
    
    try:
        with open(inacal_file, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                line = line.strip()
                
                # Ignorar líneas vacías
                if not line:
                    continue
                
                # Parsear la línea (formato: Artículo|CÓDIGO)
                if '|' not in line:
                    log.warning(f"Línea {line_number} con formato incorrecto: {line}")
                    errors += 1
                    continue
                
                parts = line.split('|')
                if len(parts) != 2:
                    log.warning(f"Línea {line_number} con formato incorrecto: {line}")
                    errors += 1
                    continue
                
                article_name = parts[0].strip()
                code = parts[1].strip()
                
                # Validar que el código no esté vacío
                if not code or not article_name:
                    log.warning(f"Línea {line_number} con datos vacíos: {line}")
                    errors += 1
                    continue
                
                # Verificar si el código ya existe
                if db.code_exists(code):
                    log.debug(f"Código duplicado (omitido): {code}")
                    duplicates += 1
                    continue
                
                # Insertar en la base de datos
                try:
                    db.save_generated_code(
                        code=code,
                        article_name=article_name,
                        notes="Migrado desde archivo histórico"
                    )
                    migrated += 1
                    
                    if migrated % 100 == 0:
                        log.info(f"Progreso: {migrated} códigos migrados...")
                        
                except Exception as e:
                    log.error(f"Error al insertar código {code}: {e}")
                    errors += 1
        
        # Resumen
        log.info("="*60)
        log.info("Migración completada")
        log.info("="*60)
        log.info(f"✓ Códigos migrados: {migrated}")
        log.info(f"⚠ Códigos duplicados (omitidos): {duplicates}")
        log.info(f"✗ Errores: {errors}")
        log.info(f"📊 Total procesado: {migrated + duplicates + errors}")
        log.info("="*60)
        
        # Registrar en base de datos
        db.log_to_database(
            module='migration',
            action='migrate_inacal_codes',
            level='INFO',
            message=f"Migración completada: {migrated} códigos",
            extra_data={
                'migrated': migrated,
                'duplicates': duplicates,
                'errors': errors
            }
        )
        
        return migrated, duplicates, errors
        
    except Exception as e:
        log.error(f"Error durante la migración: {e}")
        log.exception(e)
        return migrated, duplicates, errors + 1


def verify_migration():
    """
    Verifica que la migración fue exitosa.
    """
    db = get_db()
    
    # Contar códigos en la base de datos
    result = db.fetch_one("SELECT COUNT(*) as count FROM generated_codes")
    total_codes = result['count'] if result else 0
    
    log.info(f"Total de códigos en base de datos: {total_codes}")
    
    # Mostrar algunos ejemplos
    if total_codes > 0:
        log.info("\nEjemplos de códigos migrados:")
        examples = db.fetch_all(
            "SELECT article_name, code, created_at FROM generated_codes LIMIT 5"
        )
        for example in examples:            log.info(f"  - {example['article_name']}: {example['code']}")
    
    return total_codes


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SGDI - Migración de Códigos INACAL")
    print("="*60 + "\n")
    
    # Ejecutar migración
    migrated, duplicates, errors = migrate_inacal_codes()
    
    # Verificar
    print("\nVerificando migración...")
    total = verify_migration()
    
    print("\n" + "="*60)
    print("Proceso completado")
    print("="*60)
    
    # Código de salida
    sys.exit(0 if errors == 0 else 1)
