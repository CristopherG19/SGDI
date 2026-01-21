"""
SGDI - Ventana Principal
========================

Ventana principal de la aplicación con sidebar de navegación y área de contenido.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, Callable, Optional

from config.settings import Settings
from core.utils.logger import get_logger
from gui.components.sidebar import Sidebar
from gui.components.header import Header

log = get_logger(__name__)


class MainWindow:
    """Ventana principal de la aplicación SGDI."""
    
    def __init__(self, root: ttk.Window):
        """
        Inicializa la ventana principal.
        
        Args:
            root: Ventana raíz de ttkbootstrap
        """
        self.root = root
        self.current_tab = None
        self.tabs: Dict[str, ttk.Frame] = {}
        
        # Configurar ventana
        self._configure_window()
        
        # Crear estructura principal
        self._create_main_structure()
        
        # Cargar módulos disponibles
        self._register_modules()
        
        # Mostrar dashboard por defecto
        self.show_tab("dashboard")
        
        log.info("Ventana principal inicializada")
    
    def _configure_window(self):
        """Configura las propiedades de la ventana principal."""
        self.root.title(Settings.WINDOW_TITLE)
        
        # Tamaño de ventana
        width, height = map(int, Settings.WINDOW_SIZE.split('x'))
        self.root.geometry(f"{width}x{height}")
        
        # Centrar ventana
        self.root.place_window_center()
        
        # Configurar grid
        self.root.columnconfigure(0, weight=0)  # Sidebar (fijo)
        self.root.columnconfigure(1, weight=1)  # Contenido (expandible)
        self.root.rowconfigure(0, weight=0)     # Header (fijo)
        self.root.rowconfigure(1, weight=1)     # Contenido (expandible)
        self.root.rowconfigure(2, weight=0)     # Status bar (fijo)
    
    def _create_main_structure(self):
        """Crea la estructura principal de la ventana."""
        # Header (barra superior)
        self.header = Header(self.root, self)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Sidebar (navegación lateral)
        self.sidebar = Sidebar(self.root, self)
        self.sidebar.grid(row=1, column=0, sticky="ns", padx=0, pady=0)
        
        # Área de contenido principal
        self.content_frame = ttk.Frame(self.root, padding=0)
        self.content_frame.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Status bar (barra inferior)
        self.status_bar = ttk.Label(
            self.root,
            text="Listo",
            relief=SUNKEN,
            anchor=W,
            padding=(10, 4),
            bootstyle="inverse-secondary"
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
    
    def _register_modules(self):
        """Registra todos los módulos disponibles."""
        # Importar módulos dinámicamente cuando estén listos
        # Por ahora, usamos el dashboard como ejemplo
        
        from modules.dashboard.gui.dashboard_tab import DashboardTab
        from modules.qr_suite.gui.generador_qr_tab import GeneradorQRTab
        
        self.register_tab("dashboard", "Dashboard", DashboardTab)
        self.register_tab("qr_generator", "Generador QR", GeneradorQRTab)
        
        # TODO: Agregar otros módulos cuando estén implementados
        # self.register_tab("qr_suite", "Suite QR", QRSuiteTab)
        # self.register_tab("file_management", "Archivos", FileManagementTab)
        # self.register_tab("pdf_tools", "PDF", PDFToolsTab)
        # self.register_tab("file_auditor", "Auditoría", FileAuditorTab)
        # self.register_tab("code_generator", "Códigos", CodeGeneratorTab)
    
    def register_tab(self, tab_id: str, tab_name: str, tab_class: type):
        """
        Registra un nuevo tab en la aplicación.
        
        Args:
            tab_id: ID único del tab
            tab_name: Nombre a mostrar
            tab_class: Clase del tab (debe aceptar parent en __init__)
        """
        try:
            # Crear instancia del tab (lazy loading)
            self.tabs[tab_id] = {
                'name': tab_name,
                'class': tab_class,
                'instance': None  # Se crea cuando se muestra por primera vez
            }
            log.debug(f"Tab registrado: {tab_id} - {tab_name}")
        except Exception as e:
            log.error(f"Error al registrar tab {tab_id}: {e}")
    
    def show_tab(self, tab_id: str):
        """
        Muestra un tab específico.
        
        Args:
            tab_id: ID del tab a mostrar
        """
        if tab_id not in self.tabs:
            log.warning(f"Tab no encontrado: {tab_id}")
            self.set_status_message(f"Módulo '{tab_id}' no disponible", "warning")
            return
        
        try:
            # Ocultar tab actual si existe
            if self.current_tab and self.tabs[self.current_tab].get('instance'):
                current_instance = self.tabs[self.current_tab]['instance']
                if hasattr(current_instance, 'grid_forget'):
                    current_instance.grid_forget()
            
            # Crear instancia del tab si no existe (lazy loading)
            if self.tabs[tab_id]['instance'] is None:
                tab_class = self.tabs[tab_id]['class']
                self.tabs[tab_id]['instance'] = tab_class(self.content_frame)
                log.debug(f"Tab creado: {tab_id}")
            
            # Mostrar nuevo tab
            tab_instance = self.tabs[tab_id]['instance']
            tab_instance.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # Actualizar estado
            self.current_tab = tab_id
            tab_name = self.tabs[tab_id]['name']
            self.set_status_message(f"Módulo activo: {tab_name}")
            
            # Notificar al header
            if hasattr(self.header, 'update_current_module'):
                self.header.update_current_module(tab_name)
            
            log.info(f"Tab mostrado: {tab_id}")
            
        except Exception as e:
            log.error(f"Error al mostrar tab {tab_id}: {e}")
            log.exception(e)
            self.set_status_message(f"Error al cargar módulo: {str(e)}", "danger")
    
    def set_status_message(self, message: str, style: str = "info"):
        """
        Actualiza el mensaje de la barra de estado.
        
        Args:
            message: Mensaje a mostrar
            style: Estilo del mensaje (info, success, warning, danger)
        """
        self.status_bar.config(text=message)
        
        # Cambiar color según estilo
        if style == "success":
            self.status_bar.config(bootstyle="inverse-success")
        elif style == "warning":
            self.status_bar.config(bootstyle="inverse-warning")
        elif style == "danger":
            self.status_bar.config(bootstyle="inverse-danger")
        else:
            self.status_bar.config(bootstyle="inverse-secondary")
        
        # Auto-resetear después de 5 segundos (excepto errores)
        if style != "danger":
            self.root.after(5000, lambda: self.set_status_message("Listo"))
    
    def refresh_current_tab(self):
        """Refresca el tab actual."""
        if self.current_tab and self.tabs[self.current_tab].get('instance'):
            tab_instance = self.tabs[self.current_tab]['instance']
            if hasattr(tab_instance, 'refresh'):
                tab_instance.refresh()
                self.set_status_message("Vista actualizada", "success")
                log.debug(f"Tab refrescado: {self.current_tab}")
    
    def get_current_tab_id(self) -> Optional[str]:
        """Retorna el ID del tab actual."""
        return self.current_tab
    
    def get_tab_instance(self, tab_id: str) -> Optional[object]:
        """
        Obtiene la instancia de un tab.
        
        Args:
            tab_id: ID del tab
            
        Returns:
            Instancia del tab o None
        """
        if tab_id in self.tabs:
            return self.tabs[tab_id].get('instance')
        return None
