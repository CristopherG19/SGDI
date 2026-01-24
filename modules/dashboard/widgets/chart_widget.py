"""
SGDI - Widget de Gráfico
=========================

Widget reutilizable para mostrar gráficos con matplotlib.
"""

import tkinter as tk
import ttkbootstrap as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from core.utils.logger import get_logger

log = get_logger(__name__)


class ChartWidget(ttk.Frame):
    """Widget para mostrar gráficos."""
    
    def __init__(self, parent, title: str = "", width: int = 400, height: int = 300):
        """
        Inicializa el widget.
        
        Args:
            parent: Widget padre
            title: Título del gráfico
            width: Ancho en pixels
            height: Alto en pixels
        """
        super().__init__(parent, padding=5)
        
        self.title = title
        self.width = width
        self.height = height
        
        # Configurar matplotlib para usar estilo moderno
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Crear figura
        self.fig = Figure(figsize=(width/100, height/100), dpi=100, facecolor='#f8f9fa')
        self.ax = self.fig.add_subplot(111)
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        log.debug(f"ChartWidget creado: {title}")
    
    def bar_chart(self, labels: list, values: list, color: str = '#0d6efd', title: str = None):
        """
        Crea gráfico de barras.
        
        Args:
            labels: Etiquetas del eje X
            values: Valores del eje Y
            color: Color de las barras
            title: Título (opcional, usa self.title si no se provee)
        """
        self.ax.clear()
        
        bars = self.ax.bar(labels, values, color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
        
        # Agregar valores en las barras
        for bar in bars:
            height = bar.get_height()
            self.ax.text(
                bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=9, fontweight='bold'
            )
        
        self.ax.set_title(title or self.title, fontsize=12, fontweight='bold', pad=10)
        self.ax.set_ylabel('Cantidad', fontsize=10)
        self.ax.grid(True, alpha=0.3, axis='y')
        
        # Rotar labels si son muchos
        if len(labels) > 5:
            self.ax.tick_params(axis='x', rotation=45)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def line_chart(self, x_data: list, y_data: list, color: str = '#198754', title: str = None):
        """
        Crea gráfico de líneas.
        
        Args:
            x_data: Datos del eje X
            y_data: Datos del eje Y
            color: Color de la línea
            title: Título
        """
        self.ax.clear()
        
        self.ax.plot(x_data, y_data, color=color, marker='o', linewidth=2, markersize=6, alpha=0.8)
        self.ax.fill_between(x_data, y_data, alpha=0.2, color=color)
        
        self.ax.set_title(title or self.title, fontsize=12, fontweight='bold', pad=10)
        self.ax.set_ylabel('Cantidad', fontsize=10)
        self.ax.grid(True, alpha=0.3)
        
        # Rotar labels
        if len(x_data) > 5:
            self.ax.tick_params(axis='x', rotation=45)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def pie_chart(self, labels: list, values: list, colors: list = None, title: str = None):
        """
        Crea gráfico circular.
        
        Args:
            labels: Etiquetas
            values: Valores
            colors: Colores (opcional)
            title: Título
        """
        self.ax.clear()
        
        if not colors:
            colors = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6c757d']
        
        wedges, texts, autotexts = self.ax.pie(
            values,
            labels=labels,
            colors=colors[:len(values)],
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 9}
        )
        
        # Mejorar legibilidad
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        self.ax.set_title(title or self.title, fontsize=12, fontweight='bold', pad=10)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def horizontal_bar(self, labels: list, values: list, color: str = '#6610f2', title: str = None):
        """
        Crea gráfico de barras horizontales.
        
        Args:
            labels: Etiquetas
            values: Valores
            color: Color
            title: Título
        """
        self.ax.clear()
        
        bars = self.ax.barh(labels, values, color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
        
        # Agregar valores
        for i, (bar, value) in enumerate(zip(bars, values)):
            self.ax.text(
                value, i,
                f' {int(value):,}',
                va='center', ha='left', fontsize=9, fontweight='bold'
            )
        
        self.ax.set_title(title or self.title, fontsize=12, fontweight='bold', pad=10)
        self.ax.set_xlabel('Cantidad', fontsize=10)
        self.ax.grid(True, alpha=0.3, axis='x')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def clear(self):
        """Limpia el gráfico."""
        self.ax.clear()
        self.canvas.draw()
