"""
Script de migración de códigos desde archivos Excel
====================================================

Lee TODOS los archivos Excel de C:\INACAL-PDF\ y migra los códigos a la BD.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Agregar ruta del proyecto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database.simple_db import get_db
from core.utils.logger import get_logger

log = get_logger(__name__)


def migrate_from_excel_folder(folder_path: str = r"C:\INACAL-PDF"):
    """Migra todos los códigos desde archivos Excel."""
    print("="*70)
    print(" MIGRACIÓN MASIVA DE CÓDIGOS DESDE EXCEL ".center(70))
    print("="*70)
    print()
    
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"❌ ERROR: Carpeta no encontrada:")
        print(f"   {folder_path}")
        return
    
    print(f"📂 Carpeta: {folder}")
    print()
    
    # Buscar archivos Excel
    print("🔍 Buscando archivos Excel...")
    excel_files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls"))
    
    # Filtrar solo los que parecen ser de códigos generados
    codigo_files = [f for f in excel_files if "codigo" in f.name.lower()]
    
    print(f"✅ Encontrados {len(codigo_files)} archivos de códigos")
    print()
    
    if not codigo_files:
        print("⚠️  No se encontraron archivos Excel de códigos")
        print("    Buscando archivos con 'codigo' en el nombre...")
        return
    
    # Mostrar archivos encontrados
    print("📄 Archivos a procesar:")
    for idx, f in enumerate(codigo_files[:10], 1):
        print(f"  {idx}. {f.name}")
    if len(codigo_files) > 10:
        print(f"  ... y {len(codigo_files) - 10} archivos más")
    print()
    
    # Confirmar
    response = input(f"¿Procesar {len(codigo_files)} archivos? (s/n): ")
    if response.lower() != 's':
        print("❌ Cancelado")
        return
    
    print()
    print("="*70)
    print(" PROCESANDO ARCHIVOS ".center(70))
    print("="*70)
    print()
    
    # Conectar BD
    db = get_db()
    existing_codes = set(db.get_all_codes())
    
    total_rows = 0
    total_imported = 0
    total_skipped = 0
    total_errors = 0
    
    # Procesar cada archivo
    for idx, excel_file in enumerate(codigo_files, 1):
        print(f"[{idx}/{len(codigo_files)}] {excel_file.name}...")
        
        try:
            # Leer Excel
            df = pd.read_excel(excel_file)
            
            # Buscar columna de códigos
            codigo_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if 'codigo' in col_lower or 'code' in col_lower:
                    if 'seguridad' in col_lower or col == 'Código':
                        codigo_col = col
                        break
            
            if codigo_col is None:
                # Intentar segunda columna por defecto
                if len(df.columns) >= 2:
                    codigo_col = df.columns[1]
                else:
                    print(f"  ⚠️  No se encontró columna de códigos")
                    total_errors += 1
                    continue
            
            # Buscar columna de artículo/serie
            articulo_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if 'articulo' in col_lower or 'serie' in col_lower or 'nro' in col_lower:
                    articulo_col = col
                    break
            
            if articulo_col is None and len(df.columns) >= 1:
                articulo_col = df.columns[0]
            
            # Procesar filas
            file_imported = 0
            file_skipped = 0
            
            for _, row in df.iterrows():
                total_rows += 1
                
                try:
                    codigo = str(row[codigo_col]).strip()
                    articulo = str(row[articulo_col]).strip() if articulo_col else "Importado"
                    
                    # Validar código
                    if not codigo or codigo == 'nan' or len(codigo) < 8:
                        continue
                    
                    # Verificar duplicados
                    if codigo in existing_codes:
                        file_skipped += 1
                        total_skipped += 1
                        continue
                    
                    # Guardar
                    db.save_generated_code(codigo, articulo)
                    existing_codes.add(codigo)
                    file_imported += 1
                    total_imported += 1
                    
                except Exception as e:
                    total_errors += 1
                    continue
            
            print(f"  ✅ {file_imported} importados | ⏭️  {file_skipped} duplicados")
            
            # Mostrar progreso global cada 10 archivos
            if idx % 10 == 0:
                print(f"\n  📊 Progreso global: {total_imported} códigos importados\n")
            
        except Exception as e:
            print(f"  ❌ Error al leer archivo: {e}")
            total_errors += 1
            continue
    
    print()
    print("="*70)
    print(" RESULTADO FINAL ".center(70))
    print("="*70)
    print(f"📁 Archivos procesados: {len(codigo_files)}")
    print(f"📝 Filas analizadas:    {total_rows}")
    print(f"✅ Códigos importados:  {total_imported}")
    print(f"⏭️  Códigos duplicados:  {total_skipped}")
    print(f"❌ Errores:             {total_errors}")
    print(f"📊 Total en BD:         {len(db.get_all_codes())}")
    print("="*70)
    print()
    
    if total_imported > 0:
        print("✅ ¡Migración masiva completada!")
        print()
        print(f"Se importaron {total_imported:,} códigos históricos.")
        print("El generador NUNCA repetirá estos códigos.")
    else:
        print("ℹ️  No se importaron códigos nuevos (todos ya existían)")
    
    print()


if __name__ == "__main__":
    try:
        print()
        migrate_from_excel_folder()
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        log.error(f"Error en migración masiva: {e}")
    finally:
        print()
        input("Presiona ENTER para salir...")
