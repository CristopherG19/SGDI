"""
SGDI - Dashboard
================

Panel de control con métricas y estadísticas del sistema.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from core.database.simple_db import get_db
from core.utils.logger import get_logger

log = get_logger(__name__)


class DashboardTab(ttk.Frame):
    """Tab del Dashboard principal."""
    
    def __init__(self, parent):
        """
        Inicializa el dashboard.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent, padding=20)
        
        self.db = get_db()
        
        # Configurar grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        
        # Crear componentes
        self._create_header()
        self._create_stats_cards()
        self._create_recent_activity()
        
        # Cargar datos iniciales
        self.refresh()
        
        log.debug("Dashboard inicializado")
    
    def _create_header(self):
        """Crea el encabezado del dashboard."""
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        ttk.Label(
            header_frame,
            text="📊 Dashboard",
            font=("Segoe UI", 24, "bold"),
            bootstyle="primary"
        ).pack(side=LEFT)
        
        # Última actualización
        self.last_update_label = ttk.Label(
            header_frame,
            text="",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        )
        self.last_update_label.pack(side=RIGHT, padx=10)
    
    def _create_stats_cards(self):
        """Crea las tarjetas de estadísticas."""
        # Frame para las tarjetas
        stats_frame = ttk.Frame(self)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Configurar columnas
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
        
        # Tarjeta 1: Códigos Generados
        self.codes_card = self._create_stat_card(
            stats_frame,
            "🔢 Códigos Generados",
            "0",
            "Total en el sistema",
            "primary",
            0
        )
        
        # Tarjeta 2: Operaciones QR Hoy
        self.qr_card = self._create_stat_card(
            stats_frame,
            "🔲 Operaciones QR",
            "0",
            "Hoy",
            "info",
            1
        )
        
        # Tarjeta 3: Espacio Ahorrado
        self.space_card = self._create_stat_card(
            stats_frame,
            "💾 Espacio Ahorrado",
            "0 MB",
            "Compresiones PDF",
            "success",
            2
        )
        
        # Tarjeta 4: Búsquedas Hoy
        self.searches_card = self._create_stat_card(
            stats_frame,
            "🔍 Búsquedas",
            "0",
            "Hoy",
            "warning",
            3
        )
    
    def _create_stat_card(self, parent, title, value, subtitle, style, column):
        """
        Crea una tarjeta de estadística.
        
        Args:
            parent: Widget padre
            title: Título de la tarjeta
            value: Valor a mostrar
            subtitle: Subtítulo
            style: Estilo (primary, info, success, warning)
            column: Columna donde colocar
            
        Returns:
            Diccionario con referencias a los labels
        """
        card_frame = ttk.LabelFrame(
            parent,
            text=title,
            padding=15,
            bootstyle=style
        )
        card_frame.grid(row=0, column=column, sticky="ew", padx=5)
        
        # Valor principal
        value_label = ttk.Label(
            card_frame,
            text=value,
            font=("Segoe UI", 32, "bold"),
            bootstyle=style
        )
        value_label.pack()
        
        # Subtítulo
        subtitle_label = ttk.Label(
            card_frame,
            text=subtitle,
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        subtitle_label.pack()
        
        return {
            'frame': card_frame,
            'value': value_label,
            'subtitle': subtitle_label
        }
    
    def _create_recent_activity(self):
        """Crea la sección de actividad reciente."""
        # Frame izquierdo: Logs recientes
        left_frame = ttk.LabelFrame(
            self,
            text="📜 Actividad Reciente",
            padding=15
        )
        left_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        self.rowconfigure(2, weight=1)
        
        # Crear Treeview para logs
        columns = ('Hora', 'Módulo', 'Acción')
        self.logs_tree = ttk.Treeview(
            left_frame,
            columns=columns,
            show='headings',
            height=10,
            bootstyle="primary"
        )
        
        # Configurar columnas
        self.logs_tree.heading('Hora', text='Hora')
        self.logs_tree.heading('Módulo', text='Módulo')
        self.logs_tree.heading('Acción', text='Acción')
        
        self.logs_tree.column('Hora', width=120)
        self.logs_tree.column('Módulo', width=150)
        self.logs_tree.column('Acción', width=250)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            left_frame,
            orient=VERTICAL,
            command=self.logs_tree.yview
        )
        self.logs_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        self.logs_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Frame derecho: Información del sistema
        right_frame = ttk.LabelFrame(
            self,
            text="ℹ️ Información del Sistema",
            padding=15
        )
        right_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 0))
        
        # Información
        info_text = f"""
        Sistema: {Settings.APP_NAME} v{Settings.APP_VERSION}
        
        Base de Datos: SQLite
        Tema: {Settings.THEME}
        
        Estado: ✅ Operativo
        
        Módulos Disponibles:
        • Dashboard
        • Suite QR (En desarrollo)
        • Gestión de Archivos (En desarrollo)
        • Herramientas PDF (En desarrollo)
        • Auditoría de Archivos (En desarrollo)
        • Generador de Códigos (En desarrollo)
        
        Fase actual: 2 - Infraestructura GUI
        Progreso: ~28%
        """
        
        ttk.Label(
            right_frame,
            text=info_text.strip(),
            font=("Segoe UI", 10),
            justify=LEFT
        ).pack(fill=BOTH, expand=YES)
    
    def refresh(self):
        """Actualiza los datos del dashboard."""
        try:
            # Obtener estadísticas
            stats = self.db.get_dashboard_stats()
            
            # Actualizar tarjetas
            self.codes_card['value'].config(
                text=str(stats.get('total_codes_generated', 0))
            )
            
            self.qr_card['value'].config(
                text=str(stats.get('qr_operations_today', 0))
            )
            
            space_saved = stats.get('total_space_saved_mb', 0)
            self.space_card['value'].config(
                text=f"{space_saved:.1f} MB"
            )
            
            self.searches_card['value'].config(
                text=str(stats.get('searches_today', 0))
            )
            
            # Actualizar logs recientes
            self._update_recent_logs()
            
            # Actualizar timestamp
            now = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.config(
                text=f"Última actualización: {now}"
            )
            
            log.debug("Dashboard actualizado")
            
        except Exception as e:
            log.error(f"Error al actualizar dashboard: {e}")
    
    def _update_recent_logs(self):
        """Actualiza la lista de logs recientes."""
        try:
            # Limpiar árbol
            for item in self.logs_tree.get_children():
                self.logs_tree.delete(item)
            
            # Obtener logs recientes
            logs = self.db.get_recent_logs(limit=20)
            
            # Insertar en el árbol
            for log_entry in logs:
                # Formatear hora
                timestamp = log_entry.get('created_at', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        hora = dt.strftime("%H:%M:%S")
                    except:
                        hora = timestamp[:8]
                else:
                    hora = "--:--:--"
                
                module = log_entry.get('module_name', 'N/A')
                action = log_entry.get('action', 'N/A')
                
                # Insertar
                self.logs_tree.insert(
                    '',
                    'end',
                    values=(hora, module, action)
                )
                
        except Exception as e:
            log.error(f"Error al actualizar logs: {e}")


# Importar Settings para la info
from config.settings import Settings
