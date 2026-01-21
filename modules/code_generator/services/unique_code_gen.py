"""
SGDI - Servicio Generador de Códigos INACAL
============================================

Servicio para generación de códigos únicos alfanuméricos estilo INACAL.
Formato: XXXX999999 (4 letras + 6 números = 10 caracteres)
"""

import random
import string
from typing import List, Tuple, Optional
from pathlib import Path

from core.utils.logger import get_logger, log_operation
from core.database.simple_db import get_db
from core.utils.validators import validate_inacal_code

log = get_logger(__name__)


class CodeGenerator:
    """Generador de códigos únicos INACAL."""
    
    def __init__(self):
        """Inicializa el generador."""
        self.db = get_db()
    
    def generate_code(self, 
                     prefix: str = "",
                     length: int = 10) -> Tuple[bool, str]:
        """
        Genera un código único.
        
        Args:
            prefix: Prefijo opcional (máx 4 letras)
            length: Longitud total del código (default 10)
            
        Returns:
            Tupla (éxito, código)
        """
        try:
            if prefix:
                # Validar prefijo
                if len(prefix) > 4 or not prefix.isalpha():
                    return False, "Prefijo inválido (máx 4 letras)"
                
                prefix = prefix.upper()
                remaining = length - len(prefix)
                
                # Generar parte numérica
                suffix = ''.join(random.choices(string.digits, k=remaining))
                code = prefix + suffix
            else:
                # Formato estándar: 4 letras + 6 números
                letters = ''.join(random.choices(string.ascii_uppercase, k=4))
                numbers = ''.join(random.choices(string.digits, k=6))
                code = letters + numbers
            
            # Validar código
            valid, msg = validate_inacal_code(code)
            if not valid:
                return False, msg
            
            # Verificar unicidad
            if self.db.code_exists(code):
                # Reintentar (máx 3 veces)
                for _ in range(3):
                    return self.generate_code(prefix, length)
                return False, "No se pudo generar código único"
            
            log.debug(f"Código generado: {code}")
            return True, code
            
        except Exception as e:
            error_msg = f"Error al generar código: {e}"
            log.error(error_msg)
            return False, error_msg
    
    def generate_batch(self,
                      count: int,
                      prefix: str = "",
                      article_prefix: str = "Artículo",
                      save_to_db: bool = True) -> Tuple[List[str], List[str]]:
        """
        Genera múltiples códigos únicos.
        
        Args:
            count: Cantidad de códigos a generar
            prefix: Prefijo opcional para códigos
            article_prefix: Prefijo para nombre de artículo
            save_to_db: Si se guardan en BD
            
        Returns:
            Tupla (códigos_exitosos, errores)
        """
        import time
        start_time = time.time()
        
        successful = []
        errors = []
        
        log.info(f"Generando {count} códigos INACAL...")
        
        for i in range(count):
            success, code = self.generate_code(prefix)
            
            if success:
                successful.append(code)
                
                # Guardar en BD
                if save_to_db:
                    try:
                        article_name = f"{article_prefix} {i+1}"
                        self.db.save_generated_code(code, article_name)
                    except Exception as e:
                        log.warning(f"No se pudo guardar código {code} en BD: {e}")
            else:
                errors.append(f"Error al generar código {i+1}: {code}")
                log.warning(f"Fallo al generar código {i+1}: {code}")
        
        duration = time.time() - start_time
        
        # Log de operación
        log_operation(
            module="code_generator",
            action="generate_batch",
            success=len(errors) == 0,
            message=f"Generados {len(successful)} de {count} códigos en {duration:.2f}s",
            total=count,
            success_count=len(successful),
            error_count=len(errors)
        )
        
        return successful, errors
    
    def export_to_file(self,
                      codes: List[str],
                      output_path: str | Path,
                      format: str = "txt") -> Tuple[bool, str]:
        """
        Exporta códigos a archivo.
        
        Args:
            codes: Lista de códigos
            output_path: Ruta de salida
            format: Formato (txt, csv, excel)
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            output_path = Path(output_path)
            
            if format == "txt":
                with open(output_path, 'w', encoding='utf-8') as f:
                    for code in codes:
                        f.write(f"{code}\n")
            
            elif format == "csv":
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Código', 'Artículo'])
                    for i, code in enumerate(codes, 1):
                        writer.writerow([code, f'Artículo {i}'])
            
            elif format == "excel":
                import pandas as pd
                df = pd.DataFrame({
                    'Código': codes,
                    'Artículo': [f'Artículo {i}' for i in range(1, len(codes) + 1)]
                })
                df.to_excel(output_path, index=False, sheet_name='Códigos')
            
            else:
                return False, f"Formato no soportado: {format}"
            
            log.info(f"Códigos exportados a: {output_path}")
            return True, str(output_path)
            
        except Exception as e:
            error_msg = f"Error al exportar: {e}"
            log.error(error_msg)
            return False, error_msg
    
    def verify_uniqueness(self, code: str) -> bool:
        """
        Verifica si un código es único.
        
        Args:
            code: Código a verificar
            
        Returns:
            True si es único, False si ya existe
        """
        return not self.db.code_exists(code)
    
    def get_total_codes(self) -> int:
        """Obtiene el total de códigos en BD."""
        codes = self.db.get_all_codes()
        return len(codes)
    
    def search_by_code(self, code: str) -> Optional[dict]:
        """
        Busca información por código de seguridad.
        
        Args:
            code: Código de seguridad a buscar
            
        Returns:
            Diccionario con la información o None si no existe
        """
        result = self.db.fetch_one(
            """
            SELECT code, meter_serial, service_type, created_at
            FROM generated_codes
            WHERE code = ?
            """,
            (code,)
        )
        return result
    
    def search_by_meter_serial(self, meter_serial: str) -> List[dict]:
        """
        Busca códigos por número de serie del medidor.
        
        Args:
            meter_serial: Número de serie a buscar
            
        Returns:
            Lista de diccionarios con los códigos encontrados
        """
        results = self.db.fetch_all(
            """
            SELECT code, meter_serial, service_type, created_at
            FROM generated_codes
            WHERE meter_serial LIKE ?
            ORDER BY created_at DESC
            """,
            (f"%{meter_serial}%",)
        )
        return results

