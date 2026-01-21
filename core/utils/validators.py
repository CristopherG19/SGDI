"""
SGDI - Validadores
==================

Funciones de validación para diferentes tipos de datos y archivos.
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from core.utils.logger import get_logger

log = get_logger(__name__)


def validate_file_exists(file_path: str | Path) -> Tuple[bool, str]:
    """
    Valida que un archivo existe.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False, f"El archivo no existe: {file_path}"
        if not path.is_file():
            return False, f"La ruta no es un archivo: {file_path}"
        return True, ""
    except Exception as e:
        return False, f"Error al validar archivo: {e}"


def validate_directory_exists(directory_path: str | Path) -> Tuple[bool, str]:
    """
    Valida que un directorio existe.
    
    Args:
        directory_path: Ruta del directorio
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return False, f"El directorio no existe: {directory_path}"
        if not path.is_dir():
            return False, f"La ruta no es un directorio: {directory_path}"
        return True, ""
    except Exception as e:
        return False, f"Error al validar directorio: {e}"


def validate_file_extension(file_path: str | Path, 
                           allowed_extensions: list[str]) -> Tuple[bool, str]:
    """
    Valida que un archivo tiene una extensión permitida.
    
    Args:
        file_path: Ruta del archivo
        allowed_extensions: Lista de extensiones permitidas (ej: ['.pdf', '.txt'])
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    try:
        path = Path(file_path)
        ext = path.suffix.lower()
        
        # Normalizar extensiones permitidas
        allowed = [e.lower() if e.startswith('.') else f'.{e.lower()}' 
                  for e in allowed_extensions]
        
        if ext not in allowed:
            return False, f"Extensión no permitida. Se esperaba: {', '.join(allowed)}"
        return True, ""
    except Exception as e:
        return False, f"Error al validar extensión: {e}"


def validate_pdf_file(file_path: str | Path) -> Tuple[bool, str]:
    """
    Valida que un archivo es un PDF válido.
    
    Args:
        file_path: Ruta del archivo PDF
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Validar extensión
    valid, msg = validate_file_extension(file_path, ['.pdf'])
    if not valid:
        return False, msg
    
    # Validar que el archivo existe
    valid, msg = validate_file_exists(file_path)
    if not valid:
        return False, msg
    
    # Validar que es un PDF real (verificar magic bytes)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False, "El archivo no es un PDF válido (header incorrecto)"
        return True, ""
    except Exception as e:
        return False, f"Error al leer PDF: {e}"


def validate_image_file(file_path: str | Path, 
                       allowed_formats: Optional[list[str]] = None) -> Tuple[bool, str]:
    """
    Valida que un archivo es una imagen válida.
    
    Args:
        file_path: Ruta del archivo de imagen
        allowed_formats: Formatos permitidos (ej: ['PNG', 'JPEG'])
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    valid, msg = validate_file_exists(file_path)
    if not valid:
        return False, msg
    
    try:
        with Image.open(file_path) as img:
            # Verificar que se puede abrir
            img.verify()
            
            # Verificar formato si se especifica
            if allowed_formats:
                if img.format not in allowed_formats:
                    return False, f"Formato no permitido. Se esperaba: {', '.join(allowed_formats)}"
        
        return True, ""
    except Exception as e:
        return False, f"El archivo no es una imagen válida: {e}"


def validate_qr_code(qr_content: str) -> Tuple[bool, str]:
    """
    Valida que el contenido de un código QR es válido.
    
    Args:
        qr_content: Contenido del código QR
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not qr_content or not qr_content.strip():
        return False, "El contenido del QR está vacío"
    
    # Longitud máxima típica de un QR
    if len(qr_content) > 4000:
        return False, "El contenido del QR es demasiado largo (máx. 4000 caracteres)"
    
    return True, ""


def validate_inacal_code(code: str) -> Tuple[bool, str]:
    """
    Valida que un código INACAL tiene el formato correcto.
    
    Args:
        code: Código a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not code or not code.strip():
        return False, "El código está vacío"
    
    # Debe tener exactamente 10 caracteres alfanuméricos en mayúsculas
    if len(code) != 10:
        return False, "El código debe tener exactamente 10 caracteres"
    
    if not code.isupper():
        return False, "El código debe estar en mayúsculas"
    
    if not code.isalnum():
        return False, "El código debe contener solo letras y números"
    
    return True, ""


def validate_excel_file(file_path: str | Path) -> Tuple[bool, str]:
    """
    Valida que un archivo es un Excel válido.
    
    Args:
        file_path: Ruta del archivo Excel
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    valid, msg = validate_file_extension(file_path, ['.xlsx', '.xls', '.xlsm'])
    if not valid:
        return False, msg
    
    valid, msg = validate_file_exists(file_path)
    if not valid:
        return False, msg
    
    # Intentar abrir con openpyxl
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True)
        wb.close()
        return True, ""
    except Exception as e:
        return False, f"El archivo no es un Excel válido: {e}"


def validate_path_writable(path: str | Path) -> Tuple[bool, str]:
    """
    Valida que se puede escribir en una ruta
    
    Args:
        path: Ruta a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    try:
        path = Path(path)
        
        # Si es un archivo, verificar el directorio padre
        if path.is_file() or not path.exists():
            directory = path.parent
        else:
            directory = path
        
        # Verificar permisos de escritura
        if not os.access(directory, os.W_OK):
            return False, f"No hay permisos de escritura en: {directory}"
        
        return True, ""
    except Exception as e:
        return False, f"Error al validar permisos: {e}"


def validate_disk_space(path: str | Path, required_mb: float) -> Tuple[bool, str]:
    """
    Valida que hay suficiente espacio en disco.
    
    Args:
        path: Ruta del disco a verificar
        required_mb: Espacio requerido en MB
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    try:
        import shutil
        
        path = Path(path)
        if path.is_file():
            path = path.parent
        
        total, used, free = shutil.disk_usage(path)
        free_mb = free / (1024 * 1024)
        
        if free_mb < required_mb:
            return False, f"Espacio insuficiente. Disponible: {free_mb:.1f} MB, Requerido: {required_mb:.1f} MB"
        
        return True, ""
    except Exception as e:
        return False, f"Error al verificar espacio en disco: {e}"


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Valida que un email tiene formato válido.
    
    Args:
        email: Email a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not email or not email.strip():
        return False, "El email está vacío"
    
    # Patrón básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "El formato del email no es válido"
    
    return True, ""


def validate_date_format(date_str: str, format: str = '%Y-%m-%d') -> Tuple[bool, str]:
    """
    Valida que una fecha tiene el formato correcto.
    
    Args:
        date_str: Fecha como string
        format: Formato esperado (por defecto: YYYY-MM-DD)
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    from datetime import datetime
    
    try:
        datetime.strptime(date_str, format)
        return True, ""
    except ValueError as e:
        return False, f"Formato de fecha inválido. Se esperaba: {format}"
    except Exception as e:
        return False, f"Error al validar fecha: {e}"


def validate_number_range(value: float, min_value: Optional[float] = None, 
                         max_value: Optional[float] = None) -> Tuple[bool, str]:
    """
    Valida que un número está en un rango válido.
    
    Args:
        value: Valor a validar
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if min_value is not None and value < min_value:
        return False, f"El valor debe ser mayor o igual a {min_value}"
    
    if max_value is not None and value > max_value:
        return False, f"El valor debe ser menor o igual a {max_value}"
    
    return True, ""


# Exportar validadores principales
__all__ = [
    'validate_file_exists',
    'validate_directory_exists',
    'validate_file_extension',
    'validate_pdf_file',
    'validate_image_file',
    'validate_qr_code',
    'validate_inacal_code',
    'validate_excel_file',
    'validate_path_writable',
    'validate_disk_space',
    'validate_email',
    'validate_date_format',
    'validate_number_range',
]
