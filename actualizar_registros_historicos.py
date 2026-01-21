"""
Script para actualizar registros históricos con nuevas columnas
================================================================

Migra datos de article_name a meter_serial para códigos históricos.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database.simple_db import get_db
from core.utils.logger import get_logger

log = get_logger(__name__)


def update_historical_records():
    """Actualiza registros históricos con las nuevas columnas."""
    print("="*70)
    print(" ACTUALIZACIÓN DE REGISTROS HISTÓRICOS ".center(70))
    print("="*70)
    print()
    
    db = get_db()
    
    # Contar registros con meter_serial NULL
    result = db.fetch_one(
        "SELECT COUNT(*) as count FROM generated_codes WHERE meter_serial IS NULL"
    )
    null_count = result['count'] if result else 0
    
    print(f"📊 Registros con meter_serial NULL: {null_count}")
    print()
    
    if null_count == 0:
        print("✅ Todos los registros ya tienen meter_serial poblado")
        return
    
    print("🔄 Actualizando registros...")
    print("   Copiando article_name → meter_serial")
    print()
    
    # Actualizar: copiar article_name a meter_serial
    db.execute(
        """
        UPDATE generated_codes 
        SET meter_serial = article_name
        WHERE meter_serial IS NULL AND article_name IS NOT NULL
        """
    )
    db.connection.commit()
    
    # Verificar
    result_after = db.fetch_one(
        "SELECT COUNT(*) as count FROM generated_codes WHERE meter_serial IS NULL"
    )
    remaining = result_after['count'] if result_after else 0
    
    updated = null_count - remaining
    
    print("="*70)
    print(" RESULTADO ".center(70))
    print("="*70)
    print(f"✅ Registros actualizados: {updated}")
    print(f"⏭️  Registros sin cambios:  {remaining}")
    print("="*70)
    print()
    
    if updated > 0:
        print("✅ ¡Actualización completada!")
        print()
        print("Ahora los códigos históricos mostrarán el número de serie.")
    
    print()


if __name__ == "__main__":
    try:
        update_historical_records()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        log.error(f"Error en actualización: {e}")
    finally:
        input("Presiona ENTER para salir...")
