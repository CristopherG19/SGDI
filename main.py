"""
SGDI - Sistema de Gestión Documental Integral
==============================================

Punto de entrada principal de la aplicación.

Autor: Antigravity AI
Fecha: 2026-01-21
Versión: 1.0.0
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import Settings
from core.utils.logger import get_logger
from gui.main_window import MainWindow

log = get_logger(__name__)


def main():
    """Función principal de la aplicación."""
    try:
        # Asegurar que los directorios existen
        Settings.ensure_directories()
        
        log.info("="*60)
        log.info(f"Iniciando {Settings.APP_NAME} v{Settings.APP_VERSION}")
        log.info("="*60)
        
        # Crear ventana principal con ttkbootstrap
        root = ttk.Window(
            themename=Settings.THEME,
            title=Settings.WINDOW_TITLE
        )
        
        # Crear ventana principal de la aplicación
        app = MainWindow(root)
        
        log.info("Aplicación inicializada correctamente")
        log.info(f"Tema: {Settings.THEME}")
        log.info(f"Base de datos: {Settings.DATABASE_PATH}")
        
        # Iniciar loop principal
        root.mainloop()
        
        log.info("Aplicación cerrada correctamente")
        
    except Exception as e:
        error_msg = f"Error crítico: {e}"
        log.error(error_msg)
        log.exception(e)
        
        print("\n" + "="*60)
        print("ERROR CRÍTICO")
        print("="*60)
        print(error_msg)
        print("\nVerifica los logs para más detalles.")
        print(f"Log ubicado en: {Settings.LOG_PATH}")
        print("="*60 + "\n")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
