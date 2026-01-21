"""
SGDI - Sistema de Logging
==========================

Sistema de logging centralizado usando loguru.
Proporciona logging a archivo con rotación automática y registro en base de datos.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional
import traceback as tb

from config.settings import Settings


class SGDILogger:
    """Clase para gestión centralizada de logging."""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Inicializa el sistema de logging."""
        if cls._initialized:
            return
        
        # Asegurar que los directorios existen
        Settings.ensure_directories()
        
        # Remover el logger por defecto
        logger.remove()
        
        # ===================================
        # Logger para consola (desarrollo)
        # ===================================
        if Settings.DEBUG_MODE:
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level="DEBUG",
                colorize=True
            )
        
        # ===================================
        # Logger para archivo (todos los niveles)
        # ===================================
        log_file = Path(Settings.LOG_PATH) / "sgdi_{time:YYYY-MM-DD}.log"
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level=Settings.LOG_LEVEL,
            rotation=f"{Settings.LOG_MAX_SIZE_MB} MB",
            retention=Settings.LOG_BACKUP_COUNT,
            compression="zip",
            enqueue=True  # Thread-safe
        )
        
        # ===================================
        # Logger para errores solamente
        # ===================================
        error_log_file = Path(Settings.LOG_PATH) / "sgdi_errors_{time:YYYY-MM-DD}.log"
        logger.add(
            str(error_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            level="ERROR",
            rotation=f"{Settings.LOG_MAX_SIZE_MB} MB",
            retention=Settings.LOG_BACKUP_COUNT,
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
        
        cls._initialized = True
        logger.info(f"Sistema de logging inicializado | Nivel: {Settings.LOG_LEVEL} | Ruta: {Settings.LOG_PATH}")
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None):
        """
        Obtiene un logger configurado.
        
        Args:
            name: Nombre del módulo (opcional)
            
        Returns:
            Logger configurado
        """
        if not cls._initialized:
            cls.initialize()
        
        if name:
            return logger.bind(name=name)
        return logger
    
    @classmethod
    def log_to_database(cls, module: str, action: str, level: str, message: str, 
                       error: Exception = None, extra_data: dict = None):
        """
        Registra un log importante en la base de datos.
        
        Args:
            module: Nombre del módulo
            action: Acción realizada
            level: Nivel de log
            message: Mensaje
            error: Excepción si hay error
            extra_data: Datos adicionales
        """
        try:
            from core.database.simple_db import get_db
            
            traceback_str = None
            if error:
                traceback_str = ''.join(tb.format_exception(
                    type(error),
                    error,
                    error.__traceback__
                ))
            
            db = get_db()
            db.log_to_database(
                module=module,
                action=action,
                level=level,
                message=message,
                traceback=traceback_str,
                extra_data=extra_data
            )
        except Exception as e:
            # Si falla el log a BD, solo loguear a archivo
            logger.error(f"Error al guardar log en base de datos: {e}")


def get_logger(name: str = None):
    """
    Función helper para obtener un logger.
    
    Args:
        name: Nombre del módulo
        
    Returns:
        Logger configurado
        
    Example:
        >>> log = get_logger(__name__)
        >>> log.info("Mensaje de prueba")
    """
    return SGDILogger.get_logger(name)


def log_operation(module: str, action: str, success: bool = True, 
                 message: str = "", error: Exception = None, **kwargs):
    """
    Helper para loguear operaciones importantes a archivo y BD.
    
    Args:
        module: Nombre del módulo
        action: Acción realizada
        success: Si la operación fue exitosa
        message: Mensaje descriptivo
        error: Excepción si hubo error
        **kwargs: Datos adicionales para extra_data
        
    Example:
        >>> log_operation(
        ...     module="qr_suite",
        ...     action="generate_qr",
        ...     success=True,
        ...     message="QR generado exitosamente",
        ...     qr_content="TEST123"
        ... )
    """
    log = get_logger(module)
    level = "INFO" if success else "ERROR"
    
    if success:
        log.info(f"[{action}] {message}")
    else:
        if error:
            log.error(f"[{action}] {message}: {str(error)}")
            log.exception(error)
        else:
            log.error(f"[{action}] {message}")
    
    # Loguear operaciones importantes a BD
    if not success or action in [
        'generate_codes', 'qr_operation', 'file_audit',
        'pdf_compression', 'file_search'
    ]:
        SGDILogger.log_to_database(
            module=module,
            action=action,
            level=level,
            message=message,
            error=error,
            extra_data=kwargs if kwargs else None
        )


# Inicializar automáticamente al importar
SGDILogger.initialize()


# Exportar para facilitar importaciones
__all__ = ['get_logger', 'log_operation', 'SGDILogger', 'logger']
