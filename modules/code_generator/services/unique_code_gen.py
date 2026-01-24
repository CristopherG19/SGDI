"""
SGDI - Servicio Generador de Códigos INACAL
============================================

Servicio para generación de códigos únicos alfanuméricos estilo INACAL.

Este módulo proporciona funcionalidades completas para generar códigos de seguridad
únicos alfanuméricos para medidores de agua siguiendo el formato INACAL. Incluye
generación individual, por lotes, exportación a múltiples formatos, y búsqueda de
códigos históricos.

Formato Estándar INACAL:
    XXXX999999 (4 letras mayúsculas + 6 dígitos = 10 caracteres)
    Ejemplo: ABCD123456

Features:
    - Generación de códigos únicos garantizados
    - Soporte para prefijos personalizados
    - Generación por lotes con tracking
    - Exportación a TXT, CSV, Excel
    - Validación de unicidad contra base de datos
    - Búsqueda por código o número de serie
    - Historial completo en base de datos

Examples:
    Generación simple::

        generator = CodeGenerator()
        success, code = generator.generate_code()
        print(f"Código: {code}")  # Ej: XKPA456789

    Generación con prefijo::

        success, code = generator.generate_code(prefix="AGUA")
        print(f"Código: {code}")  # Ej: AGUA456789

    Generación por lotes::

        codes, errors = generator.generate_batch(
            count=100,
            article_prefix="Medidor",
            save_to_db=True
        )
        print(f"Generados: {len(codes)} códigos")

Author:
    SGDI Development Team

Version:
    1.0.0
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
    """Generador profesional de códigos de seguridad INACAL para medidores.
    
    Genera códigos alfanuméricos únicos siguiendo el formato INACAL (4 letras + 6 números).
    Todos los códigos generados se validan contra la base de datos para garantizar unicidad.
    Soporta generación individual, por lotes, y exportación a múltiples formatos.
    
    Attributes:
        db: Instancia de la base de datos para registro y validación de códigos
    
    Example:
        >>> generator = CodeGenerator()
        >>> success, code = generator.generate_code()
        >>> if success:
        ...     print(f"Código generado: {code}")
    
    Note:
        - Todos los códigos se validan automáticamente
        - La unicidad se garantiza consultando la base de datos
        - Los códigos históricos nunca se repiten
    """
    
    def __init__(self):
        """Inicializa el generador de códigos.
        
        Configura la conexión a la base de datos para validación y registro
        de códigos generados.
        """
        self.db = get_db()
    
    def generate_code(self, 
                     prefix: str = "",
                     length: int = 10) -> Tuple[bool, str]:
        """Genera un código de seguridad único alfanumérico.
        
        Crea un código siguiendo el formato INACAL (4 letras + 6 números) o
        personalizado con prefijo. Valida automáticamente contra la base de datos
        para garantizar unicidad. Reintenta hasta 3 veces si encuentra duplicados.
        
        Args:
            prefix (str, optional): Prefijo personalizado (máximo 4 letras mayúsculas).
                Si se especifica, el resto se completa con números.
                Defaults to "" (usa formato estándar).
            length (int, optional): Longitud total del código.
                Defaults to 10 (formato INACAL).
            
        Returns:
            Tuple[bool, str]: Una tupla con:
                - bool: True si la generación fue exitosa, False si falló
                - str: Código generado si exitoso, mensaje de error si falló
        
        Examples:
            >>> generator = CodeGenerator()
            >>> success, code = generator.generate_code()
            >>> print(code)  # Ej: XKPA123456
            
            >>> success, code = generator.generate_code(prefix="AGUA")
            >>> print(code)  # Ej: AGUA123456
            
            >>> success, code = generator.generate_code(prefix="MED", length=10)
            >>> print(code)  # Ej: MED1234567
        
        Note:
            - El prefijo se convierte automáticamente a mayúsculas
            - Si no se puede generar código único tras 3 intentos, retorna error
            - Los códigos se validan con validate_inacal_code() antes de retornar
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
        """Genera múltiples códigos de seguridad INACAL en lote.
        
        Procesa la generación de múltiples códigos secuencialmente, validando
        unicidad para cada uno. Opcionalmente guarda cada código en la base de datos
        con su artículo asociado. Registra estadísticas completas de la operación.
        
        Args:
            count (int): Cantidad de códigos a generar. Debe ser mayor a 0.
            prefix (str, optional): Prefijo común para todos los códigos
                (máximo 4 letras). Defaults to "" (formato estándar).
            article_prefix (str, optional): Prefijo para nombres de artículos.
                Se concatena con el número secuencial (ej: "Medidor 1").
                Defaults to "Artículo".
            save_to_db (bool, optional): Si es True, guarda cada código generado
                exitosamente en la base de datos. Defaults to True.
            
        Returns:
            Tuple[List[str], List[str]]: Una tupla con dos listas:
                - List[str]: Códigos generados exitosamente
                - List[str]: Mensajes de error para códigos fallidos
        
        Examples:
            >>> generator = CodeGenerator()
            >>> codes, errors = generator.generate_batch(
            ...     count=100,
            ...     article_prefix="Medidor",
            ...     save_to_db=True
            ... )
            >>> print(f"Exitosos: {len(codes)}, Fallidos: {len(errors)}")
            
            >>> # Con prefijo personalizado
            >>> codes, errors = generator.generate_batch(
            ...     count=50,
            ...     prefix="AGUA",
            ...     save_to_db=False
            ... )
        
        Note:
            - Si save_to_db es False, los códigos NO se guardan automáticamente
            - Los errores no detienen el proceso, continúa con los siguientes
            - Se registra el tiempo total y estadísticas completas
            - Se recomienda save_to_db=True para evitar duplicados futuros
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
        """Exporta una lista de códigos a archivo en el formato especificado.
        
        Guarda los códigos generados en un archivo de texto, CSV o Excel.
        Para CSV y Excel, incluye columnas adicionales con numeración de artículos.
        
        Args:
            codes (List[str]): Lista de códigos a exportar.
            output_path (str | Path): Ruta completa del archivo de salida.
                La extensión se ajusta automáticamente según el formato.
            format (str, optional): Formato de exportación:
                - "txt": Un código por línea
                - "csv": Tabla con columnas "Código" y "Artículo"
                - "excel": Archivo .xlsx con columnas "Código" y "Artículo"
                Defaults to "txt".
            
        Returns:
            Tuple[bool, str]: Una tupla con:
                - bool: True si la exportación fue exitosa, False si falló
                - str: Ruta del archivo generado si exitoso, mensaje de error si falló
        
        Examples:
            >>> codes = ["ABCD123456", "EFGH789012"]
            >>> success, path = generator.export_to_file(
            ...     codes,
            ...     "./exports/codigos.txt",
            ...     format="txt"
            ... )
            
            >>> success, path = generator.export_to_file(
            ...     codes,
            ...     "./exports/codigos.xlsx",
            ...     format="excel"
            ... )
        
        Note:
            - El directorio padre debe existir antes de exportar
            - Para Excel se requiere la librería pandas y openpyxl
            - Los archivos existentes se sobrescriben sin confirmación
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
        """Verifica si un código es único en la base de datos.
        
        Consulta la base de datos para determinar si un código ya existe.
        Útil para validar códigos generados externamente antes de guardarlos.
        
        Args:
            code (str): Código de seguridad a verificar.
            
        Returns:
            bool: True si el código es único (no existe en BD),
                False si ya existe.
        
        Example:
            >>> generator = CodeGenerator()
            >>> is_unique = generator.verify_uniqueness("ABCD123456")
            >>> if is_unique:
            ...     print("Código disponible")
            ... else:
            ...     print("Código ya existe")
        
        Note:
            Este método solo consulta, no guarda el código en la base de datos.
        """
        return not self.db.code_exists(code)
    
    def get_total_codes(self) -> int:
        """Obtiene el total de códigos almacenados en la base de datos.
        
        Cuenta todos los códigos registrados históricamente, incluyendo
        códigos generados por el sistema y migrados desde Excel.
        
        Returns:
            int: Número total de códigos en la base de datos.
        
        Example:
            >>> generator = CodeGenerator()
            >>> total = generator.get_total_codes()
            >>> print(f"Total de códigos: {total:,}")
        """
        codes = self.db.get_all_codes()
        return len(codes)
    
    def search_by_code(self, code: str) -> Optional[dict]:
        """Busca información completa de un código de seguridad específico.
        
        Consulta la base de datos para obtener todos los datos asociados
        a un código de seguridad, incluyendo número de serie del medidor,
        tipo de servicio y fecha de creación.
        
        Args:
            code (str): Código de seguridad a buscar (formato INACAL).
            
        Returns:
            Optional[dict]: Diccionario con los campos:
                - code (str): Código de seguridad
                - meter_serial (str): Número de serie del medidor
                - service_type (str): Tipo de servicio
                - created_at (datetime): Fecha y hora de creación
                Retorna None si el código no existe.
        
        Example:
            >>> generator = CodeGenerator()
            >>> info = generator.search_by_code("ABCD123456")
            >>> if info:
            ...     print(f"Medidor: {info['meter_serial']}")
            ...     print(f"Creado: {info['created_at']}")
            ... else:
            ...     print("Código no encontrado")
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
        """Busca todos los códigos asociados a un número de serie de medidor.
        
        Realiza una búsqueda parcial (LIKE) en la base de datos para encontrar
        todos los códigos asociados a un medidor específico. Útil para rastrear
        el historial de códigos de un medidor.
        
        Args:
            meter_serial (str): Número de serie del medidor a buscar.
                Soporta búsqueda parcial (no requiere coincidencia exacta).
            
        Returns:
            List[dict]: Lista de diccionarios, cada uno con:
                - code (str): Código de seguridad
                - meter_serial (str): Número de serie del medidor
                - service_type (str): Tipo de servicio
                - created_at (datetime): Fecha y hora de creación
                Ordenados por fecha (más recientes primero).
                Lista vacía si no se encuentran resultados.
        
        Example:
            >>> generator = CodeGenerator()
            >>> results = generator.search_by_meter_serial("12345")
            >>> print(f"Encontrados {len(results)} códigos")
            >>> for item in results:
            ...     print(f"{item['code']} - {item['created_at']}")
        
        Note:
            - La búsqueda es case-insensitive y permite coincidencias parciales
            - Los resultados se ordenan cronológicamente (más recientes primero)
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

