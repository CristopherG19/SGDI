"""
SGDI - Tab Generador de Códigos INACAL
=======================================

Interfaz gráfica para generación de códigos de seguridad para medidores de agua.

Este módulo proporciona una interfaz completa para generar códigos de seguridad
INACAL, con funcionalidades de generación masiva, importación de números de serie,
búsqueda de códigos, exportación a Excel, y visualización en tabla.

Features:
    - Generación de códigos individuales o masivos
    - Importación de números de serie desde Excel/CSV
    - Búsqueda de códigos por código o número de serie
    - Exportación de resultados a Excel
    - Visualización en tabla con 3 columnas (Artículo, Nº Serie, Código)
    - Copiado rápido de códigos al portapapeles
    - Contador de códigos en tiempo real
    - Guardado automático en base de datos

UI Components:
    - Panel de búsqueda: consulta de códigos históricos
    - Panel de entrada: texto manual o importación de archivo
    - Panel de resultados: tabla con códigos generados
    - Panel de acciones: exportar, copiar, guardar

Author:
    SGDI Development Team

Version:
    1.0.0
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview
from pathlib import Path
from datetime import datetime
import pandas as pd

from modules.code_generator.services.unique_code_gen import CodeGenerator
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


class CodeGeneratorTab(ttk.Frame):
    """Tab GUI para generación de códigos de seguridad INACAL para medidores.
    
    Proporciona una interfaz completa para generar códigos de seguridad alfanuméricos
    únicos para medidores de agua. Soporta entrada manual de números de serie,
    importación desde Excel/CSV, generación masiva, búsqueda de códigos históricos,
    y exportación de resultados.
    
    Attributes:
        generator (CodeGenerator): Instancia del servicio generador de códigos
        generated_data (list): Lista de tuplas (articulo, serie, codigo) generadas
        meter_serials (tk.StringVar): Variable para entrada de números de serie
        count_var (tk.StringVar): Variable para contador de series ingresadas
    
    Example:
        >>> from tkinter import Tk
        >>> root = Tk()
        >>> tab = CodeGeneratorTab(root)
        >>> tab.pack()
    
    Workflow:
        1. Usuario ingresa números de serie (manual o importación)
        2. Click en "Generar Códigos"
        3. Sistema genera códigos únicos para cada serie
        4. Resultados se muestran en tabla
        5. Usuario puede copiar, exportar o guardar en BD
    
    Note:
        - Los códigos se generan automáticamente sin duplicados
        - Se validan contra la base de datos antes de generarse
        - Los códigos se pueden buscar posteriormente por código o serie
    """
    
    def __init__(self, parent):
        """Inicializa el tab generador de códigos con todos sus componentes.
        
        Configura las variables de control, instancia el servicio generador,
        y construye la interfaz gráfica completa con paneles de búsqueda,
        entrada, resultados y acciones.
        
        Args:
            parent (tk.Widget): Widget padre (generalmente un Notebook o Frame).
        """
        super().__init__(parent, padding=20)
        
        self.generator = CodeGenerator()
        self.generated_results = []  # [(nro_serie, codigo, tipo_servicio), ...]
        
        self._create_ui()
        log.debug("Generador de Códigos tab inicializado")
    
    def _create_ui(self):
        """Crea la interfaz."""
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        
        # Título
        ttk.Label(
            self,
            text="🔢 Generador de Códigos de Seguridad - INACAL",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Panel de búsqueda
        self._create_search_panel()
        
        # Panel izquierdo: Entrada y configuración
        self._create_input_panel()
        
        # Panel derecho: Tabla de resultados
        self._create_results_panel()
        
        # Panel inferior: Acciones
        self._create_actions_panel()
    
    def _create_search_panel(self):
        """Panel de búsqueda de códigos."""
        search_frame = ttk.LabelFrame(
            self,
            text="🔍 Búsqueda de Códigos",
            padding=15
        )
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Tipo de búsqueda
        search_type_frame = ttk.Frame(search_frame)
        search_type_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            search_type_frame,
            text="Buscar por:",
            font=("Segoe UI", 10)
        ).pack(side=LEFT, padx=(0, 10))
        
        self.search_type = tk.StringVar(value="codigo")
        
        ttk.Radiobutton(
            search_type_frame,
            text="Código de Seguridad",
            variable=self.search_type,
            value="codigo"
        ).pack(side=LEFT, padx=10)
        
        ttk.Radiobutton(
            search_type_frame,
            text="Nro de Serie",
            variable=self.search_type,
            value="serie"
        ).pack(side=LEFT, padx=10)
        
        # Campo de búsqueda
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=X)
        search_input_frame.columnconfigure(0, weight=1)
        
        self.search_entry = ttk.Entry(
            search_input_frame,
            font=("Segoe UI", 10)
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self._search_code())
        
        ttk.Button(
            search_input_frame,
            text="🔍 Buscar",
            command=self._search_code,
            bootstyle="info"
        ).grid(row=0, column=1)
        
        # Resultado de búsqueda
        self.search_result_frame = ttk.Frame(search_frame)
        self.search_result_frame.pack(fill=X, pady=(10, 0))
        
        self.search_result_label = ttk.Label(
            self.search_result_frame,
            text="",
            font=("Segoe UI", 9)
        )
        self.search_result_label.pack()
    
    def _search_code(self):
        """Busca código o nro de serie."""
        search_text = self.search_entry.get().strip()
        
        if not search_text:
            messagebox.showwarning("Advertencia", "Ingrese un valor para buscar")
            return
        
        search_type = self.search_type.get()
        
        try:
            if search_type == "codigo":
                # Buscar por código
                result = self.generator.search_by_code(search_text)
                
                if result:
                    # MySQL devuelve datetime object, no string
                    created = result['created_at']
                    if created:
                        fecha = created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created).split()[0]
                    else:
                        fecha = "N/A"
                    self.search_result_label.config(
                        text=f"✅ Encontrado:\n"
                             f"Código: {result['code']}\n"
                             f"Nro Serie: {result['meter_serial'] or 'N/A'}\n"
                             f"Tipo: {result['service_type'] or 'N/A'}\n"
                             f"Fecha: {fecha}",
                        foreground="green",
                        font=("Segoe UI", 10, "bold")
                    )
                else:
                    self.search_result_label.config(
                        text=f"❌ Código '{search_text}' no encontrado",
                        foreground="red",
                        font=("Segoe UI", 10)
                    )
            
            else:  # serie
                # Buscar por nro de serie
                results = self.generator.search_by_meter_serial(search_text)
                
                if results:
                    if len(results) == 1:
                        r = results[0]
                        created = r['created_at']
                        if created:
                            fecha = created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created).split()[0]
                        else:
                            fecha = "N/A"
                        self.search_result_label.config(
                            text=f"✅ Encontrado:\n"
                                 f"Nro Serie: {r['meter_serial']}\n"
                                 f"Código: {r['code']}\n"
                                 f"Tipo: {r['service_type'] or 'N/A'}\n"
                                 f"Fecha: {fecha}",
                            foreground="green",
                            font=("Segoe UI", 10, "bold")
                        )
                    else:
                        def format_date(dt):
                            if dt:
                                return dt.strftime('%Y-%m-%d') if hasattr(dt, 'strftime') else str(dt).split()[0]
                            return "N/A"
                        codes_list = "\n".join([f"  • {r['code']} ({r['service_type']}) - {format_date(r['created_at'])}" 
                                               for r in results[:5]])
                        self.search_result_label.config(
                            text=f"✅ {len(results)} códigos encontrados:\n{codes_list}" +
                                 (f"\n... y {len(results)-5} más" if len(results) > 5 else ""),
                            foreground="green",
                            font=("Segoe UI", 9, "bold")
                        )
                else:
                    self.search_result_label.config(
                        text=f"❌ Nro '{search_text}' no encontrado",
                        foreground="red",
                        font=("Segoe UI", 10)
                    )
        
        except Exception as e:
            log.error(f"Error en búsqueda: {e}")
            messagebox.showerror("Error", f"Error al buscar:\n{str(e)}")
    
    def _create_input_panel(self):
        """Panel de entrada."""
        input_frame = ttk.LabelFrame(
            self,
            text="📝 Datos de Entrada",
            padding=15
        )
        input_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        self.rowconfigure(2, weight=1)
        
        # Tipo de servicio
        service_frame = ttk.LabelFrame(input_frame, text="Tipo de Servicio", padding=10)
        service_frame.pack(fill=X, pady=(0, 15))
        
        self.service_type = tk.StringVar(value="VIMA")
        
        ttk.Radiobutton(
            service_frame,
            text="VIMA (Verificación Inicial)",
            variable=self.service_type,
            value="VIMA",
            bootstyle="primary"
        ).pack(anchor=W, pady=2)
        
        ttk.Radiobutton(
            service_frame,
            text="VP (Verificación Posterior)",
            variable=self.service_type,
            value="VP",
            bootstyle="primary"
        ).pack(anchor=W, pady=2)
        
        # Instrucciones
        ttk.Label(
            input_frame,
            text="Nros. de Serie de Medidores:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 5))
        
        ttk.Label(
            input_frame,
            text="Pegue o importe (uno por línea)",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 5))
        
        # Área de texto con scroll
        text_frame = ttk.Frame(input_frame)
        text_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.input_text = tk.Text(
            text_frame,
            height=12,
            width=30,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        self.input_text.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.config(command=self.input_text.yview)
        
        # Vincular eventos
        self.input_text.bind('<KeyRelease>', self._update_count)
        
        # Botones
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=X)
        
        ttk.Button(
            btn_frame,
            text="📂 Importar",
            command=self._import_file,
            bootstyle="info-outline",
            width=12
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="🗑️ Limpiar",
            command=self._clear_input,
            bootstyle="secondary-outline",
            width=12
        ).pack(side=LEFT)
        
        # Contador
        self.count_label = ttk.Label(
            input_frame,
            text="Medidores: 0",
            font=("Segoe UI", 10, "bold"),
            bootstyle="info"
        )
        self.count_label.pack(anchor=CENTER, pady=(10, 0))
    
    def _create_results_panel(self):
        """Panel de resultados con tabla."""
        results_frame = ttk.LabelFrame(
            self,
            text="✅ Códigos Generados",
            padding=15
        )
        results_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 0))
        
        # Tabla
        table_frame = ttk.Frame(results_frame)
        table_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(table_frame)
        scroll_y.pack(side=RIGHT, fill=Y)
        
        scroll_x = ttk.Scrollbar(table_frame, orient=HORIZONTAL)
        scroll_x.pack(side=BOTTOM, fill=X)
        
        # Treeview
        self.results_table = Treeview(
            table_frame,
            columns=("nro_serie", "codigo", "servicio"),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            height=15
        )
        
        # Configurar columnas
        self.results_table.heading("nro_serie", text="Nro Serie")
        self.results_table.heading("codigo", text="Código de Seguridad")
        self.results_table.heading("servicio", text="Tipo de Servicio")
        
        self.results_table.column("nro_serie", width=150, anchor=W)
        self.results_table.column("codigo", width=150, anchor=CENTER)
        self.results_table.column("servicio", width=80, anchor=CENTER)
        
        self.results_table.pack(side=LEFT, fill=BOTH, expand=YES)
        
        scroll_y.config(command=self.results_table.yview)
        scroll_x.config(command=self.results_table.xview)
        
        # Botones de acción
        btn_frame = ttk.Frame(results_frame)
        btn_frame.pack(fill=X)
        
        ttk.Button(
            btn_frame,
            text="📋 Copiar Códigos",
            command=self._copy_codes_only,
            bootstyle="success",
            width=18
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="💾 Exportar",
            command=self._export_results,
            bootstyle="info",
            width=18
        ).pack(side=LEFT)
    
    def _create_actions_panel(self):
        """Panel de acciones."""
        actions_frame = ttk.Frame(self)
        actions_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        # Botón generar (centrado)
        btn_container = ttk.Frame(actions_frame)
        btn_container.pack()
        
        ttk.Button(
            btn_container,
            text="🎲 Generar Códigos de Seguridad",
            command=self._generate_codes,
            bootstyle="success",
            width=35
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_container,
            text="💾 Guardar en BD",
            command=self._save_to_db,
            bootstyle="primary",
            width=20
        ).pack(side=LEFT, padx=5)
        
        # Estadísticas
        stats_frame = ttk.LabelFrame(actions_frame, text="📊 Estadísticas", padding=10)
        stats_frame.pack(fill=X, pady=(15, 0))
        
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack()
        
        ttk.Label(
            stats_container,
            text=f"Total en BD: {self.generator.get_total_codes()}",
            font=("Segoe UI", 10, "bold"),
            bootstyle="info"
        ).pack(side=LEFT, padx=20)
        
        self.session_label = ttk.Label(
            stats_container,
            text="Generados ahora: 0",
            font=("Segoe UI", 10, "bold"),
            bootstyle="success"
        )
        self.session_label.pack(side=LEFT, padx=20)
    
    def _update_count(self, event=None):
        """Actualiza contador."""
        text = self.input_text.get("1.0", END).strip()
        if text:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            self.count_label.config(text=f"Medidores: {len(lines)}")
        else:
            self.count_label.config(text="Medidores: 0")
    
    def _clear_input(self):
        """Limpia entrada."""
        self.input_text.delete("1.0", END)
        self._update_count()
    
    def _import_file(self):
        """Importa nros de serie."""
        filename = filedialog.askopenfilename(
            title="Importar números de serie",
            filetypes=[
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Texto", "*.txt"),
                ("Todos", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            filepath = Path(filename)
            series = []
            
            if filepath.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath)
                series = df.iloc[:, 0].dropna().astype(str).tolist()
            elif filepath.suffix.lower() == '.csv':
                df = pd.read_csv(filepath)
                series = df.iloc[:, 0].dropna().astype(str).tolist()
            elif filepath.suffix.lower() == '.txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    series = [line.strip() for line in f if line.strip()]
            else:
                messagebox.showwarning("Advertencia", "Formato no soportado")
                return
            
            self.input_text.delete("1.0", END)
            self.input_text.insert("1.0", '\n'.join(series))
            self._update_count()
            
            messagebox.showinfo("Éxito", f"Se importaron {len(series)} números de serie")
            
        except Exception as e:
            log.error(f"Error al importar: {e}")
            messagebox.showerror("Error", f"No se pudo importar:\n{str(e)}")
    
    def _generate_codes(self):
        """Genera códigos."""
        text = self.input_text.get("1.0", END).strip()
        if not text:
            messagebox.showwarning("Advertencia", "Ingrese números de serie")
            return
        
        series = [line.strip() for line in text.splitlines() if line.strip()]
        
        if not series:
            messagebox.showwarning("Advertencia", "No hay números válidos")
            return
        
        tipo_servicio = self.service_type.get()
        
        # Limpiar tabla
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        
        self.generated_results = []
        
        # Generar
        for nro_serie in series:
            success, codigo = self.generator.generate_code()
            if success:
                self.generated_results.append((nro_serie, codigo, tipo_servicio))
                self.results_table.insert(
                    "",
                    END,
                    values=(nro_serie, codigo, tipo_servicio)
                )
        
        # Actualizar stats
        self.session_label.config(text=f"Generados ahora: {len(self.generated_results)}")
        
        if self.generated_results:
            messagebox.showinfo(
                "Generación Completa",
                f"✅ Se generaron {len(self.generated_results)} códigos de seguridad\n\n"
                f"Tipo de servicio: {tipo_servicio}\n\n"
                "Usa 'Copiar Códigos' para copiar solo los códigos\n"
                "o 'Exportar' para guardar la tabla completa"
            )
    
    def _copy_codes_only(self):
        """Copia SOLO los códigos al portapapeles."""
        if not self.generated_results:
            messagebox.showwarning("Advertencia", "No hay códigos para copiar")
            return
        
        # Solo columna de códigos
        codes = '\n'.join([codigo for _, codigo, _ in self.generated_results])
        
        self.clipboard_clear()
        self.clipboard_append(codes)
        
        messagebox.showinfo(
            "Copiado",
            f"✅ {len(self.generated_results)} códigos copiados\n\n"
            "Puedes pegarlos en Excel, correo, etc."
        )
    
    def _export_results(self):
        """Exporta con las 3 columnas."""
        if not self.generated_results:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = filedialog.asksaveasfilename(
            title="Exportar códigos generados",
            defaultextension=".xlsx",
            initialfile=f"codigos_seguridad_{timestamp}.xlsx",
            filetypes=[
                ("Excel", "*.xlsx"),
                ("CSV", "*.csv"),
                ("Texto", "*.txt")
            ]
        )
        
        if not filename:
            return
        
        try:
            filepath = Path(filename)
            
            # Crear DataFrame con nombres correctos
            df = pd.DataFrame(
                self.generated_results,
                columns=["Nro Serie", "Código de Seguridad", "Tipo de Servicio"]
            )
            
            if filepath.suffix.lower() == '.xlsx':
                df.to_excel(filename, index=False, sheet_name='Códigos')
            elif filepath.suffix.lower() == '.csv':
                df.to_csv(filename, index=False, encoding='utf-8')
            elif filepath.suffix.lower() == '.txt':
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Nro Serie\tCódigo de Seguridad\tTipo de Servicio\n")
                    for nro, cod, serv in self.generated_results:
                        f.write(f"{nro}\t{cod}\t{serv}\n")
            
            messagebox.showinfo("Éxito", f"✅ Exportado a:\n{filename}")
            
        except Exception as e:
            log.error(f"Error al exportar: {e}")
            messagebox.showerror("Error", f"No se pudo exportar:\n{str(e)}")
    
    def _save_to_db(self):
        """Guarda en BD con columnas separadas."""
        if not self.generated_results:
            messagebox.showwarning("Advertencia", "No hay códigos para guardar")
            return
        
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Guardar {len(self.generated_results)} códigos en la BD?"
        ):
            return
        
        try:
            for nro_serie, codigo, tipo_servicio in self.generated_results:
                # Guardar en columnas separadas
                self.generator.db.save_generated_code(
                    code=codigo,
                    meter_serial=nro_serie,
                    service_type=tipo_servicio,
                    article_name=f"{nro_serie} - {tipo_servicio}"  # Para compatibility
                )
            
            messagebox.showinfo(
                "Guardado",
                f"✅ {len(self.generated_results)} códigos guardados en BD\n\n"
                "Columnas guardadas:\n"
                "• Nro Serie (meter_serial)\n"
                "• Código de Seguridad (code)\n"
                f"• Tipo de Servicio (service_type)"
            )
            
            # Limpiar
            for item in self.results_table.get_children():
                self.results_table.delete(item)
            self.generated_results = []
            self.session_label.config(text="Generados ahora: 0")
            
        except Exception as e:
            log.error(f"Error al guardar: {e}")
            messagebox.showerror("Error", f"No se pudo guardar:\n{str(e)}")
    
    def refresh(self):
        """Refresca el tab."""
        log.debug("Generador de Códigos tab refrescado")
