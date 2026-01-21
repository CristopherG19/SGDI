"""
SGDI - Sistema de Gestión Documental Integral
==============================================

Punto de entrada principal de la aplicación.

Este sistema unifica 5 herramientas especializadas:
- QR Suite (procesamiento, lectura y generación de QR)
- File Management (búsqueda y auditoría)
- PDF Tools (compresión y optimización)
- Code Generator (códigos únicos INACAL)
- Dashboard (métricas y estadísticas)

Autor: [Tu Nombre]
Versión: 1.0.0
Fecha: 2026-01-21
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

# Importar configuración
from config.settings import Settings

# TODO: Importar ventana principal cuando esté implementada
# from gui.main_window import MainWindow


class SGDIApp:
    """Clase principal de la aplicación SGDI."""
    
    def __init__(self, root):
        self.root = root
        self.settings = Settings()
        
        # Configurar ventana principal
        self.root.title(self.settings.WINDOW_TITLE)
        self.root.geometry(self.settings.WINDOW_SIZE)
        
        # Aplicar tema
        self.style = ttk.Style(theme=self.settings.THEME)
        
        # Crear interfaz temporal
        self._create_temp_interface()
    
    def _create_temp_interface(self):
        """Crea interfaz temporal para Fase 0."""
        container = ttk.Frame(self.root, padding=40)
        container.pack(fill=BOTH, expand=YES)
        
        # Título
        ttk.Label(
            container,
            text="SGDI v1.0",
            font=("Segoe UI", 32, "bold"),
            bootstyle="inverse-primary"
        ).pack(pady=20)
        
        ttk.Label(
            container,
            text="Sistema de Gestión Documental Integral",
            font=("Segoe UI", 16),
            bootstyle="secondary"
        ).pack(pady=10)
        
        # Separador
        ttk.Separator(container, bootstyle="primary").pack(fill=X, pady=30)
        
        # Mensaje de construcción
        ttk.Label(
            container,
            text="🚧 Proyecto en Construcción 🚧",
            font=("Segoe UI", 24, "bold"),
            bootstyle="warning"
        ).pack(pady=20)
        
        ttk.Label(
            container,
            text="Fase 0: Preparación Completada ✓",
            font=("Segoe UI", 14),
            bootstyle="success"
        ).pack(pady=10)
        
        # Información
        info_frame = ttk.LabelFrame(
            container,
            text="Estado del Proyecto",
            padding=20,
            bootstyle="info"
        )
        info_frame.pack(pady=20, fill=BOTH, expand=YES)
        
        status_items = [
            "✓ Estructura de carpetas creada",
            "✓ Archivos de configuración generados",
            "✓ Requirements.txt consolidado",
            "⏳ Pendiente: Inicializar repositorio Git",
            "⏳ Pendiente: Crear entorno virtual",
            "⏳ Siguiente: Fase 1 - Core y Logging"
        ]
        
        for item in status_items:
            ttk.Label(
                info_frame,
                text=item,
                font=("Segoe UI", 12),
                bootstyle="inverse-dark" if "✓" in item else "secondary"
            ).pack(anchor=W, pady=5)
        
        # Botón de salida
        ttk.Button(
            container,
            text="Cerrar",
            command=self.root.quit,
            bootstyle="danger-outline",
            width=20
        ).pack(pady=20)
        
        # Barra de estado
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=X, side=BOTTOM)
        
        ttk.Label( container,
            text=f"Ruta del proyecto: {ROOT_DIR}",
            relief=SUNKEN,
            anchor=W,
            padding=(5, 2),
            bootstyle="inverse-secondary"
        ).pack(fill=X)


def main():
    """Función principal para ejecutar la aplicación."""
    try:
        # Crear ventana principal con tema darkly
        root = ttk.Window(themename="darkly")
        
        # Inicializar aplicación
        app = SGDIApp(root)
        
        # Centrar ventana
        root.place_window_center()
        
        # Ejecutar loop principal
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror(
            "Error Fatal",
            f"No se pudo iniciar la aplicación:\n\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
