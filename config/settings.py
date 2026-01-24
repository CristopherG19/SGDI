"""
SGDI - Configuración del Sistema
=================================

Módulo de configuración centralizada para toda la aplicación.
Lee variables de entorno desde .env y proporciona valores por defecto.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings:
    """Clase de configuración centralizada."""
    
    # Rutas del proyecto
    ROOT_DIR = Path(__file__).parent.parent
    DATA_DIR = ROOT_DIR / "data"
    DATABASE_DIR = DATA_DIR / "database"
    LOGS_DIR = DATA_DIR / "logs"
    EXPORTS_DIR = DATA_DIR / "exports"
    ASSETS_DIR = ROOT_DIR / "assets"
    
    # Configuración General
    APP_NAME = os.getenv("APP_NAME", "SGDI")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # Base de Datos
    DB_TYPE = os.getenv("DB_TYPE", "mysql")  # 'sqlite' o 'mysql'
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATABASE_DIR / "sgdi.db"))  # Para SQLite
    
    # Configuración MySQL
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "sgdi")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")
    
    # Rutas de Trabajo
    DEFAULT_EXPORT_PATH = os.getenv("DEFAULT_EXPORT_PATH", "C:/SGDI/exports")
    DEFAULT_TEMP_PATH = os.getenv("DEFAULT_TEMP_PATH", "C:/SGDI/temp")
    LOG_PATH = os.getenv("LOG_PATH", str(LOGS_DIR))
    
    # Configuración PDF
    PDF_COMPRESSION_QUALITY = int(os.getenv("PDF_COMPRESSION_QUALITY", "70"))
    PDF_MAX_IMAGE_DPI = int(os.getenv("PDF_MAX_IMAGE_DPI", "150"))
    
    # Configuración QR
    QR_DEFAULT_SIZE = int(os.getenv("QR_DEFAULT_SIZE", "300"))
    QR_ERROR_CORRECTION = os.getenv("QR_ERROR_CORRECTION", "H")
    
    # Configuración INACAL
    INACAL_CODES_PATH = os.getenv(
        "INACAL_CODES_PATH",
        "C:/INACAL-PDF/codigos_unicos.txt"
    )
    INACAL_EXPORT_PATH = os.getenv("INACAL_EXPORT_PATH", "C:/INACAL-PDF")
    
    # Configuración UI
    THEME = os.getenv("THEME", "darkly")
    WINDOW_SIZE = os.getenv("WINDOW_SIZE", "1400x900")
    WINDOW_TITLE = os.getenv(
        "WINDOW_TITLE",
        f"{APP_NAME} v{APP_VERSION} - Sistema de Gestión Documental Integral"
    )
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_MAX_SIZE_MB = int(os.getenv("LOG_MAX_SIZE_MB", "10"))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    @classmethod
    def ensure_directories(cls):
        """Crea los directorios necesarios si no existen."""
        directories = [
            cls.DATA_DIR,
            cls.DATABASE_DIR,
            cls.LOGS_DIR,
            cls.EXPORTS_DIR,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_info(cls):
        """Retorna información de configuración actual."""
        return {
            "app_name": cls.APP_NAME,
            "version": cls.APP_VERSION,
            "debug": cls.DEBUG_MODE,
            "theme": cls.THEME,
            "database": cls.DATABASE_PATH,
            "log_level": cls.LOG_LEVEL,
        }
