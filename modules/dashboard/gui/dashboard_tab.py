"""
SGDI - Dashboard Avanzado
==========================

Panel de control con gráficos y métricas reales del sistema.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from core.database.simple_db import get_db
from core.utils.logger import get_logger
from config.settings import Settings
from modules.dashboard.services.stats_analyzer import StatsAnalyzer
from modules.dashboard.widgets.chart_widget import ChartWidget

log = get_logger(__name__)


class DashboardTab(ttk.Frame):
    """Tab del Dashboard con gráficos y métricas reales."""
    
    def __init__(self, parent):
        """Inicializa el dashboard."""
        super().__init__(parent, padding=20)
        
        self.db = get_db()
        self.analyzer = StatsAnalyzer()
        
        # Configurar grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        
        # Crear componentes
        self._create_header()
        self._create_stats_cards()
        self._create_charts()
        self._create_activity_section()
        
        # Cargar datos iniciales
        self.refresh()
        
        log.debug("Dashboard avanzado inicializado")
    
    def _create_header(self):
        """Crea el encabezado."""
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
        self.last_update_label.pack(side=RIGHT)
    
    def _create_stats_cards(self):
        """Crea las tarjetas de estadísticas."""
        stats_frame = ttk.Frame(self)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
        
        # Tarjetas
        self.codes_card = self._create_stat_card(
            stats_frame, "🔢 Códigos INACAL", "0", "Total", "primary", 0
        )
        
        self.qr_card = self._create_stat_card(
            stats_frame, "🔲 QR Generados", "0", "Total", "info", 1
        )
        
        self.space_card = self._create_stat_card(
            stats_frame, "💾 Espacio Ahorrado", "0 MB", "PDFs", "success", 2
        )
        
        self.files_card = self._create_stat_card(
            stats_frame, "🔍 Archivos Hallados", "0", "Total", "warning", 3
        )
    
    def _create_stat_card(self, parent, title, value, subtitle, style, column):
        """Crea una tarjeta de estadística."""
        card_frame = ttk.LabelFrame(
            parent,
            text=title,
            padding=12,
            bootstyle=style
        )
        card_frame.grid(row=0, column=column, sticky="ew", padx=5)
        
        value_label = ttk.Label(
            card_frame,
            text=value,
            font=("Segoe UI", 28, "bold"),
            bootstyle=style
        )
        value_label.pack()
        
        subtitle_label = ttk.Label(
            card_frame,
            text=subtitle,
            font=("Segoe UI", 9),
            bootstyle="secondary"
        )
        subtitle_label.pack()
        
        return {'value': value_label, 'subtitle': subtitle_label}
    
    def _create_charts(self):
        """Crea los gráficos."""
        charts_frame = ttk.Frame(self)
        charts_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 15))
        self.rowconfigure(2, weight=1)
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        
        # Gráfico 1: Uso de módulos (barras horizontales)
        chart1_frame = ttk.LabelFrame(
            charts_frame,
            text="📈 Uso de Módulos (Top 5)",
            padding=10
        )
        chart1_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.module_chart = ChartWidget(chart1_frame, width=400, height=250)
        self.module_chart.pack(fill=BOTH, expand=YES)
        
        # Gráfico 2: Códigos por tipo (pie)
        chart2_frame = ttk.LabelFrame(
            charts_frame,
            text="📊 Códigos INACAL por Tipo",
            padding=10
        )
        chart2_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self.codes_chart = ChartWidget(chart2_frame, width=400, height=250)
        self.codes_chart.pack(fill=BOTH, expand=YES)
    
    def _create_activity_section(self):
        """Crea sección de actividad."""
        activity_frame = ttk.LabelFrame(
            self,
            text="📜 Actividad Reciente",
            padding=15
        )
        activity_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.rowconfigure(3, weight=1)
        
        # Treeview
        columns = ('Hora', 'Módulo', 'Acción', 'Estado')
        self.activity_tree = ttk.Treeview(
            activity_frame,
            columns=columns,
            show='headings',
            height=6,
            bootstyle="primary"
        )
        
        self.activity_tree.heading('Hora', text='Hora')
        self.activity_tree.heading('Módulo', text='Módulo')
        self.activity_tree.heading('Acción', text='Acción')
        self.activity_tree.heading('Estado', text='Estado')
        
        self.activity_tree.column('Hora', width=100)
        self.activity_tree.column('Módulo', width=150)
        self.activity_tree.column('Acción', width=300)
        self.activity_tree.column('Estado', width=80)
        
        scrollbar = ttk.Scrollbar(
            activity_frame,
            orient=VERTICAL,
            command=self.activity_tree.yview
        )
        self.activity_tree.configure(yscrollcommand=scrollbar.set)
        
        self.activity_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def refresh(self):
        """Actualiza todos los datos del dashboard."""
        try:
            # Obtener resumen completo
            summary = self.analyzer.get_summary()
            
            # Actualizar tarjetas
            self._update_cards(summary)
            
            # Actualizar gráficos
            self._update_charts(summary)
            
            # Actualizar actividad
            self._update_activity(summary)
            
            # Timestamp
            now = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.config(text=f"Última actualización: {now}")
            
            log.debug("Dashboard actualizado")
            
        except Exception as e:
            log.error(f"Error actualizando dashboard: {e}")
    
    def _update_cards(self, summary: dict):
        """Actualiza las tarjetas de estadísticas."""
        # Códigos INACAL
        codes_total = summary['codes']['total']
        self.codes_card['value'].config(text=f"{codes_total:,}")
        
        # QR
        qr_total = summary['qr']['total']
        self.qr_card['value'].config(text=f"{qr_total:,}")
        
        # Espacio ahorrado
        space_mb = summary['file_ops']['space_saved_mb']
        self.space_card['value'].config(text=f"{space_mb:.1f} MB")
        
        # Archivos encontrados
        files_found = summary['file_ops']['files_found']
        self.files_card['value'].config(text=f"{files_found:,}")
    
    def _update_charts(self, summary: dict):
        """Actualiza los gráficos."""
        # Gráfico 1: Uso de módulos
        module_usage = summary['module_usage'][:5]  # Top 5
        if module_usage:
            labels = [m[0] for m in module_usage]
            values = [m[1] for m in module_usage]
            self.module_chart.horizontal_bar(labels, values, color='#0d6efd')
        else:
            self.module_chart.clear()
        
        # Gráfico 2: Códigos por tipo
        codes_by_type = summary['codes']['by_type']
        if codes_by_type:
            labels = list(codes_by_type.keys())
            values = list(codes_by_type.values())
            self.codes_chart.pie_chart(labels, values)
        else:
            self.codes_chart.clear()
    
    def _update_activity(self, summary: dict):
        """Actualiza actividad reciente."""
        # Limpiar
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        
        # Agregar
        for activity in summary['recent_activity']:
            timestamp = activity.get('created_at', '')
            try:
                dt = datetime.fromisoformat(timestamp)
                hora = dt.strftime("%H:%M:%S")
            except:
                hora = "--:--:--"
            
            module = activity.get('module', 'N/A')
            action = activity.get('action', 'N/A')
            success = activity.get('success', True)
            estado = "✓" if success else "✗"
            
            self.activity_tree.insert(
                '',
                'end',
                values=(hora, module, action, estado),
                tags=('success' if success else 'error',)
            )
        
        # Colorear
        self.activity_tree.tag_configure('success', foreground='#28a745')
        self.activity_tree.tag_configure('error', foreground='#dc3545')
