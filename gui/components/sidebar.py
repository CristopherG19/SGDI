"""
SGDI - Sidebar de Navegación
=============================

Componente de navegación lateral con menú de módulos.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from core.utils.logger import get_logger

log = get_logger(__name__)


class Sidebar(ttk.Frame):
    """Sidebar de navegación lateral."""
    
    def __init__(self, parent, main_window):
        """
        Inicializa el sidebar.
        
        Args:
            parent: Widget padre
            main_window: Referencia a MainWindow
        """
        super().__init__(parent, bootstyle="dark", padding=0)
        
        self.main_window = main_window
        self.buttons = {}
        self.current_button = None
        
        # Configurar frame
        self.configure(width=250)
        
        # Crear componentes
        self._create_header()
        self._create_menu()
        self._create_footer()
    
    def _create_header(self):
        """Crea el encabezado del sidebar."""
        header_frame = ttk.Frame(self, bootstyle="primary", padding=15)
        header_frame.pack(fill=X, pady=(0, 10))
        
        # Logo/Título
        ttk.Label(
            header_frame,
            text="SGDI",
            font=("Segoe UI", 20, "bold"),
            bootstyle="inverse-primary"
        ).pack(anchor=W)
        
        ttk.Label(
            header_frame,
            text="v1.0.0",
            font=("Segoe UI", 9),
            bootstyle="inverse-primary"
        ).pack(anchor=W)
    
    def _create_menu(self):
        """Crea el menú de navegación."""
        menu_frame = ttk.Frame(self, padding=(10, 5))
        menu_frame.pack(fill=BOTH, expand=YES)
        
        # Definir elementos del menú
        menu_items = [
            {
                'id': 'dashboard',
                'icon': '📊',
                'text': 'Dashboard',
                'description': 'Vista general'
            },
            {
                'separator': True
            },
            {
                'id': 'qr_generator',
                'icon': '🔲',
                'text': 'Generador QR',
                'description': 'Códigos QR simples'
            },
            {
                'id': 'qr_reader',
                'icon': '📖',
                'text': 'Lector QR',
                'description': 'Leer y renombrar'
            },
            {
                'id': 'excel_processor',
                'icon': '📊',
                'text': 'Procesador Excel',
                'description': 'Excel + QR + PDF'
            },
            {
                'id': 'file_search',
                'icon': '🔍',
                'text': 'Buscador',
                'description': 'Búsqueda y copia archivos'
            },
            {
                'id': 'pdf_compressor',
                'icon': '📄',
                'text': 'Compresor PDF',
                'description': 'Compresión de PDFs'
            },
            {
                'id': 'file_auditor',
                'icon': '🔍',
                'text': 'Auditor',
                'description': 'Verificación de archivos'
            },
            {
                'id': 'code_generator',
                'icon': '🔢',
                'text': 'Códigos',
                'description': 'INACAL'
            },
            {
                'id': 'dropbox_extractor',
                'icon': '☁️',
                'text': 'Dropbox',
                'description': 'Extractor de URLs'
            },
        ]
        
        # Crear botones
        for item in menu_items:
            if item.get('separator'):
                ttk.Separator(menu_frame, bootstyle="secondary").pack(
                    fill=X, pady=8, padx=10
                )
            else:
                self._create_menu_button(menu_frame, item)
    
    def _create_menu_button(self, parent, item):
        """
        Crea un botón de menú.
        
        Args:
            parent: Widget padre
            item: Diccionario con datos del botón
        """
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=2, padx=5)
        
        # Botón principal
        btn = ttk.Button(
            btn_frame,
            text=f"{item['icon']}  {item['text']}",
            command=lambda: self._on_menu_click(item['id']),
            bootstyle="light-outline",
            cursor="hand2"
        )
        btn.pack(fill=X, ipady=8)
        
        # Tooltip/descripción
        if item.get('description'):
            # Crear tooltip simple
            def on_enter(e):
                self.main_window.set_status_message(item['description'])
            
            def on_leave(e):
                if self.main_window.current_tab == item['id']:
                    self.main_window.set_status_message(
                        f"Módulo activo: {item['text']}"
                    )
                else:
                    self.main_window.set_status_message("Listo")
            
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
        
        # Guardar referencia
        self.buttons[item['id']] = btn
    
    def _on_menu_click(self, tab_id: str):
        """
        Maneja el click en un botón del menú.
        
        Args:
            tab_id: ID del tab a mostrar
        """
        # Resetear estilo del botón anterior
        if self.current_button and self.current_button in self.buttons:
            self.buttons[self.current_button].config(
                bootstyle="light-outline"
            )
        
        # Aplicar estilo activo al botón actual
        if tab_id in self.buttons:
            self.buttons[tab_id].config(bootstyle="primary")
            self.current_button = tab_id
        
        # Mostrar el tab
        self.main_window.show_tab(tab_id)
        
        log.debug(f"Navegación: {tab_id}")
    
    def _create_footer(self):
        """Crea el pie del sidebar."""
        footer_frame = ttk.Frame(self, padding=10)
        footer_frame.pack(fill=X, side=BOTTOM)
        
        # Información adicional
        ttk.Label(
            footer_frame,
            text="Sistema de Gestión\nDocumental Integral",
            font=("Segoe UI", 8),
            bootstyle="light",
            justify=CENTER
        ).pack()
    
    def set_active(self, tab_id: str):
        """
        Marca un tab como activo visualmente.
        
        Args:
            tab_id: ID del tab
        """
        self._on_menu_click(tab_id)
