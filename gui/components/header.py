"""
SGDI - Header (Barra Superior)
===============================

Componente de barra superior con información y acciones rápidas.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from config.settings import Settings
from core.utils.logger import get_logger

log = get_logger(__name__)


class Header(ttk.Frame):
    """Header (barra superior) de la aplicación."""
    
    def __init__(self, parent, main_window):
        """
        Inicializa el header.
        
        Args:
            parent: Widget padre
            main_window: Referencia a MainWindow
        """
        super().__init__(parent, bootstyle="primary", padding=12)
        
        self.main_window = main_window
        self.current_module_label = None
        
        # Crear componentes
        self._create_left_section()
        self._create_center_section()
        self._create_right_section()
        
        # Iniciar reloj
        self._update_clock()
    
    def _create_left_section(self):
        """Crea la sección izquierda (título y módulo actual)."""
        left_frame = ttk.Frame(self, bootstyle="primary")
        left_frame.pack(side=LEFT, fill=Y)
        
        # Título
        ttk.Label(
            left_frame,
            text="SGDI",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-primary"
        ).pack(side=LEFT, padx=(0, 15))
        
        # Separador
        ttk.Separator(left_frame, orient=VERTICAL, bootstyle="light").pack(
            side=LEFT, fill=Y, padx=10
        )
        
        # Módulo actual
        self.current_module_label = ttk.Label(
            left_frame,
            text="Dashboard",
            font=("Segoe UI", 11),
            bootstyle="inverse-primary"
        )
        self.current_module_label.pack(side=LEFT)
    
    def _create_center_section(self):
        """Crea la sección central (acciones rápidas)."""
        center_frame = ttk.Frame(self, bootstyle="primary")
        center_frame.pack(side=LEFT, expand=YES, fill=BOTH, padx=20)
        
        # Botón de refrescar
        ttk.Button(
            center_frame,
            text="🔄 Actualizar",
            command=self._on_refresh,
            bootstyle="light-outline",
            cursor="hand2"
        ).pack(side=LEFT, padx=5)
    
    def _create_right_section(self):
        """Crea la sección derecha (info del sistema y reloj)."""
        right_frame = ttk.Frame(self, bootstyle="primary")
        right_frame.pack(side=RIGHT, fill=Y)
        
        # Reloj
        self.clock_label = ttk.Label(
            right_frame,
            text="",
            font=("Segoe UI", 10),
            bootstyle="inverse-primary"
        )
        self.clock_label.pack(side=RIGHT, padx=(15, 0))
        
        # Separador
        ttk.Separator(right_frame, orient=VERTICAL, bootstyle="light").pack(
            side=RIGHT, fill=Y, padx=10
        )
        
        # Info
        ttk.Label(
            right_frame,
            text=f"v{Settings.APP_VERSION}",
            font=("Segoe UI", 9),
            bootstyle="inverse-primary"
        ).pack(side=RIGHT, padx=5)
    
    def _update_clock(self):
        """Actualiza el reloj en tiempo real."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%d/%m/%Y")
        
        self.clock_label.config(text=f"{date_str} {time_str}")
        
        # Actualizar cada segundo
        self.after(1000, self._update_clock)
    
    def _on_refresh(self):
        """Maneja el click en el botón de refrescar."""
        self.main_window.refresh_current_tab()
        log.debug("Vista refrescada desde header")
    
    def update_current_module(self, module_name: str):
        """
        Actualiza el nombre del módulo actual mostrado.
        
        Args:
            module_name: Nombre del módulo
        """
        if self.current_module_label:
            self.current_module_label.config(text=module_name)
