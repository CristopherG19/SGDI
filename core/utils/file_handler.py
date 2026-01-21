"""
SGDI - Manejador de Archivos
=============================

Utilidades para operaciones comunes con archivos y directorios.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Callable, Tuple
import hashlib

from core.utils.logger import get_logger

log = get_logger(__name__)


def ensure_directory(path: str | Path) -> Path:
    """
    Asegura que un directorio existe, creándolo si es necesario.
    
    Args:
        path: Ruta del directorio
        
    Returns:
        Path object del directorio
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_file_operation(operation: Callable, *args, **kwargs) -> Tuple[bool, Optional[str]]:
    """
    Ejecuta una operación de archivo de forma segura.
    
    Args:
        operation: Función a ejecutar
        *args: Argumentos posicionales
        **kwargs: Argumentos con nombre
        
    Returns:
        Tupla (éxito: bool, error: str o None)
    """
    try:
        operation(*args, **kwargs)
        return True, None
    except PermissionError as e:
        error_msg = f"Permiso denegado: {e}"
        log.error(error_msg)
        return False, error_msg
    except FileNotFoundError as e:
        error_msg = f"Archivo no encontrado: {e}"
        log.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error inesperado: {e}"
        log.exception(e)
        return False, error_msg


def copy_file(source: str | Path, destination: str | Path, 
              preserve_metadata: bool = True) -> bool:
    """
    Copia unarchivo de forma segura.
    
    Args:
        source: Ruta del archivo fuente
        destination: Ruta de destino
        preserve_metadata: Si preservar metadatos (fecha, permisos)
        
    Returns:
        True si fue exitoso
    """
    try:
        if preserve_metadata:
            shutil.copy2(source, destination)
        else:
            shutil.copy(source, destination)
        log.debug(f"Archivo copiado: {source} → {destination}")
        return True
    except Exception as e:
        log.error(f"Error al copiar archivo {source}: {e}")
        return False


def move_file(source: str | Path, destination: str | Path) -> bool:
    """
    Mueve un archivo de forma segura.
    
    Args:
        source: Ruta del archivo fuente
        destination: Ruta de destino
        
    Returns:
        True si fue exitoso
    """
    try:
        shutil.move(str(source), str(destination))
        log.debug(f"Archivo movido: {source} → {destination}")
        return True
    except Exception as e:
        log.error(f"Error al mover archivo {source}: {e}")
        return False


def delete_file(path: str | Path, safe: bool = True) -> bool:
    """
    Elimina un archivo de forma segura.
    
    Args:
        path: Ruta del archivo
        safe: Si True, no lanza excepciones si el archivo no existe
        
    Returns:
        True si fue exitoso
    """
    try:
        Path(path).unlink()
        log.debug(f"Archivo eliminado: {path}")
        return True
    except FileNotFoundError:
        if safe:
            return True
        log.warning(f"Archivo no encontrado: {path}")
        return False
    except Exception as e:
        log.error(f"Error al eliminar archivo {path}: {e}")
        return False


def get_file_size(path: str | Path) -> Optional[int]:
    """
    Obtiene el tamaño de un archivo en bytes.
    
    Args:
        path: Ruta del archivo
        
    Returns:
        Tamaño en bytes o None si hay error
    """
    try:
        return Path(path).stat().st_size
    except Exception as e:
        log.error(f"Error al obtener tamaño de {path}: {e}")
        return None


def get_file_size_mb(path: str | Path) -> Optional[float]:
    """
    Obtiene el tamaño de un archivo en megabytes.
    
    Args:
        path: Ruta del archivo
        
    Returns:
        Tamaño en MB o None si hay error
    """
    size_bytes = get_file_size(path)
    return round(size_bytes / (1024 * 1024), 2) if size_bytes else None


def find_files(directory: str | Path, pattern: str = "*", 
               recursive: bool = True, file_type: Optional[str] = None) -> List[Path]:
    """
    Busca archivos en un directorio.
    
    Args:
        directory: Directorio donde buscar
        pattern: Patrón de búsqueda (glob)
        recursive: Si buscar en subdirectorios
        file_type: Extensión de archivo (ej: '.pdf', '.txt')
        
    Returns:
        Lista de rutas encontradas
    """
    directory = Path(directory)
    
    if not directory.exists():
        log.warning(f"Directorio no existe: {directory}")
        return []
    
    try:
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        # Filtrar solo archivos (no directorios)
        files = [f for f in files if f.is_file()]
        
        # Filtrar por tipo si se especifica
        if file_type:
            if not file_type.startswith('.'):
                file_type = f'.{file_type}'
            files = [f for f in files if f.suffix.lower() == file_type.lower()]
        
        log.debug(f"Encontrados {len(files)} archivos en {directory}")
        return files
        
    except Exception as e:
        log.error(f"Error al buscar archivos en {directory}: {e}")
        return []


def get_directory_size(directory: str | Path) -> Tuple[int, int]:
    """
    Calcula el tamaño total de un directorio.
    
    Args:
        directory: Ruta del directorio
        
    Returns:
        Tupla (tamaño_bytes, cantidad_archivos)
    """
    directory = Path(directory)
    total_size = 0
    file_count = 0
    
    try:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        return total_size, file_count
    except Exception as e:
        log.error(f"Error al calcular tamaño de {directory}: {e}")
        return 0, 0


def calculate_file_hash(file_path: str | Path, algorithm: str = 'md5') -> Optional[str]:
    """
    Calcula el hash de un archivo.
    
    Args:
        file_path: Ruta del archivo
        algorithm: Algoritmo de hash ('md5', 'sha256', etc.)
        
    Returns:
        Hash del archivo o None si hay error
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        log.error(f"Error al calcular hash de {file_path}: {e}")
        return None


def is_path_safe(path: str | Path, base_directory: Optional[str | Path] = None) -> bool:
    """
    Verifica si una ruta es segura (no sale del directorio base).
    
    Args:
        path: Ruta a verificar
        base_directory: Directorio base permitido
        
    Returns:
        True si la ruta es segura
    """
    try:
        path = Path(path).resolve()
        
        if base_directory:
            base = Path(base_directory).resolve()
            # Verificar que la ruta está dentro del directorio base
            return str(path).startswith(str(base))
        
        # Si no hay directorio base, solo verificar que la ruta no tiene '..'
        return '..' not in Path(path).parts
        
    except Exception:
        return False


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres no permitidos.
    
    Args:
        filename: Nombre de archivo original
        replacement: Carácter de reemplazo
        
    Returns:
        Nombre de archivo sanitizado
    """
    # Caracteres no permitidos en Windows
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, replacement)
    
    # Remover espacios al inicio y final
    filename = filename.strip()
    
    # Asegurar que no termine con punto (no permitido en Windows)
    while filename.endswith('.'):
        filename = filename[:-1]
    
    return filename


def create_backup(file_path: str | Path, backup_suffix: str = '.bak') -> Optional[Path]:
    """
    Crea una copia de respaldo de un archivo.
    
    Args:
        file_path: Ruta del archivo original
        backup_suffix: Sufijo para el archivo de respaldo
        
    Returns:
        Ruta del archivo de respaldo o None si hay error
    """
    try:
        file_path = Path(file_path)
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        
        shutil.copy2(file_path, backup_path)
        log.info(f"Backup creado: {backup_path}")
        return backup_path
        
    except Exception as e:
        log.error(f"Error al crear backup de {file_path}: {e}")
        return None


def get_temp_file(prefix: str = 'sgdi_', suffix: str = '.tmp', 
                 directory: Optional[str | Path] = None) -> Path:
    """
    Genera una ruta para un archivo temporal único.
    
    Args:
        prefix: Prefijo del nombre de archivo
        suffix: Sufijo/extensión del archivo
        directory: Directorio donde crear el temporal
        
    Returns:
        Ruta del archivo temporal
    """
    import tempfile
    import uuid
    
    if directory is None:
        from config.settings import Settings
        directory = Settings.DEFAULT_TEMP_PATH
    
    ensure_directory(directory)
    
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{prefix}{unique_id}{suffix}"
    
    return Path(directory) / filename


# Exportar funciones principales
__all__ = [
    'ensure_directory',
    'safe_file_operation',
    'copy_file',
    'move_file',
    'delete_file',
    'get_file_size',
    'get_file_size_mb',
    'find_files',
    'get_directory_size',
    'calculate_file_hash',
    'is_path_safe',
    'sanitize_filename',
    'create_backup',
    'get_temp_file',
]
