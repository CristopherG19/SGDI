"""
SGDI - Tab Procesador de Excel
===============================

Interfaz para procesar archivos Excel y generar documentos con QR.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path
from threading import Thread

from modules.qr_suite.services.excel_processor import ExcelProcessor
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


class ProcesadorExcelTab(ttk.Frame):
    """Tab para procesamiento de Excel con QR."""
    
    def __init__(self, parent):
        """Inicializa el tab."""
        super().__init__(parent, padding=20)
        
        self.processor = ExcelProcessor()
        self.is_processing = False
        
        # Variables
        self.archivo_excel = tk.StringVar()
        self.hoja_plantilla = tk.StringVar()
        self.hoja_datos = tk.StringVar(value="DATA")
        self.carpeta_salida = tk.StringVar(value=str(Settings.EXPORTS_DIR))
        self.columna_clave = tk.IntVar(value=0)
        self.modo_avanzado = tk.BooleanVar(value=False)
        self.generar_pdf = tk.BooleanVar(value=True)
        self.imprimir = tk.BooleanVar(value=False)
        self.copias = tk.IntVar(value=1)
        
        self.hojas_disponibles = []
        
        self._create_ui()
        log.debug("Procesador Excel tab inicializado")
    
    def _create_ui(self):
        """Crea la interfaz."""
        self.columnconfigure(0, weight=1)
        
        # Título
        ttk.Label(
            self,
            text="📊 Procesador de Excel con QR",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        # Panel de archivo
        self._create_file_panel()
        
        # Panel de configuración
        self._create_config_panel()
        
        # Panel de modo avanzado
        self._create_advanced_panel()
        
        # Botones de acción
        self._create_action_panel()
        
        # Barra de progreso
        self._create_progress_panel()
        
        # Log
        self._create_log_panel()
    
    def _create_file_panel(self):
        """Panel de selección de archivo."""
        file_frame = ttk.LabelFrame(
            self,
            text="📂 Archivo de Datos",
            padding=15
        )
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Archivo Excel:").grid(row=0, column=0, sticky=W, padx=(0, 10))
        
        ttk.Entry(
            file_frame,
            textvariable=self.archivo_excel,
            state="readonly",
            font=("Segoe UI", 9)
        ).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        ttk.Button(
            file_frame,
            text="Examinar",
            command=self._select_excel,
            bootstyle="info"
        ).grid(row=0, column=2)
    
    def _create_config_panel(self):
        """Panel de configuración básica."""
        config_frame = ttk.LabelFrame(
            self,
            text="⚙️ Configuración",
            padding=15
        )
        config_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # Fila 1: Hojas
        ttk.Label(config_frame, text="Hoja de datos:").grid(row=0, column=0, sticky=W, pady=5)
        self.combo_datos = ttk.Combobox(
            config_frame,
            textvariable=self.hoja_datos,
            state="readonly",
            width=25
        )
        self.combo_datos.grid(row=0, column=1, sticky=W, padx=5)
        
        ttk.Label(config_frame, text="Columna clave:").grid(row=0, column=2, sticky=W, padx=(20, 10))
        ttk.Spinbox(
            config_frame,
            from_=0,
            to=50,
            textvariable=self.columna_clave,
            width=5
        ).grid(row=0, column=3, sticky=W)
        
        # Fila 2: Carpeta salida
        ttk.Label(config_frame, text="Carpeta salida:").grid(row=1, column=0, sticky=W, pady=5)
        ttk.Entry(
            config_frame,
            textvariable=self.carpeta_salida,
            width=40
        ).grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)
        
        ttk.Button(
            config_frame,
            text="...",
            command=self._select_output_folder,
            width=3
        ).grid(row=1, column=3)
    
    def _create_advanced_panel(self):
        """Panel de opciones avanzadas (COM)."""
        advanced_frame = ttk.LabelFrame(
            self,
            text="🔧 Modo Avanzado (requiere Excel instalado)",
            padding=15
        )
        advanced_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        # Checkbox modo avanzado
        ttk.Checkbutton(
            advanced_frame,
            text="Activar modo avanzado (plantillas + PDF + impresión)",
            variable=self.modo_avanzado,
            command=self._toggle_advanced,
            bootstyle="primary"
        ).grid(row=0, column=0, columnspan=4, sticky=W, pady=(0, 10))
        
        # Opciones avanzadas (inicialmente deshabilitadas)
        self.adv_widgets = []
        
        # Plantilla
        lbl1 = ttk.Label(advanced_frame, text="Hoja plantilla:")
        lbl1.grid(row=1, column=0, sticky=W, pady=5)
        self.combo_plantilla = ttk.Combobox(
            advanced_frame,
            textvariable=self.hoja_plantilla,
            state=DISABLED,
            width=25
        )
        self.combo_plantilla.grid(row=1, column=1, sticky=W, padx=5)
        self.adv_widgets.extend([self.combo_plantilla])
        
        # Generar PDF
        self.chk_pdf = ttk.Checkbutton(
            advanced_frame,
            text="Generar PDF",
            variable=self.generar_pdf,
            state=DISABLED
        )
        self.chk_pdf.grid(row=2, column=0, sticky=W, pady=5)
        self.adv_widgets.append(self.chk_pdf)
        
        # Imprimir
        self.chk_print = ttk.Checkbutton(
            advanced_frame,
            text="Imprimir",
            variable=self.imprimir,
            state=DISABLED
        )
        self.chk_print.grid(row=2, column=1, sticky=W)
        self.adv_widgets.append(self.chk_print)
        
        lbl2 = ttk.Label(advanced_frame, text="Copias:")
        lbl2.grid(row=2, column=2, sticky=W, padx=(20, 5))
        self.spin_copias = ttk.Spinbox(
            advanced_frame,
            from_=1,
            to=10,
            textvariable=self.copias,
            width=5,
            state=DISABLED
        )
        self.spin_copias.grid(row=2, column=3, sticky=W)
        self.adv_widgets.append(self.spin_copias)
    
    def _create_action_panel(self):
        """Panel de botones de acción."""
        action_frame = ttk.Frame(self)
        action_frame.grid(row=4, column=0, pady=15)
        
        self.btn_process = ttk.Button(
            action_frame,
            text="🚀 Procesar Excel",
            command=self._start_processing,
            bootstyle="success",
            width=25
        )
        self.btn_process.pack(side=LEFT, padx=10)
        
        self.btn_stop = ttk.Button(
            action_frame,
            text="⏹️ Detener",
            command=self._stop_processing,
            bootstyle="danger",
            state=DISABLED,
            width=15
        )
        self.btn_stop.pack(side=LEFT, padx=10)
    
    def _create_progress_panel(self):
        """Panel de progreso."""
        progress_frame = ttk.Frame(self)
        progress_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            bootstyle="success-striped"
        )
        self.progress.grid(row=0, column=0, sticky="ew")
        
        self.lbl_progress = ttk.Label(
            progress_frame,
            text="Esperando archivo...",
            font=("Segoe UI", 9)
        )
        self.lbl_progress.grid(row=1, column=0, sticky=W, pady=(5, 0))
    
    def _create_log_panel(self):
        """Panel de log."""
        log_frame = ttk.LabelFrame(
            self,
            text="📋 Log de Proceso",
            padding=10
        )
        log_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 0))
        self.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Consolas", 9),
            state=NORMAL
        )
        self.log_text.pack(fill=BOTH, expand=YES)
        
        # Tags de colores
        self.log_text.tag_config("INFO", foreground="#17a2b8")
        self.log_text.tag_config("SUCCESS", foreground="#28a745")
        self.log_text.tag_config("WARNING", foreground="#ffc107")
        self.log_text.tag_config("ERROR", foreground="#dc3545")
    
    def _toggle_advanced(self):
        """Activa/desactiva opciones avanzadas."""
        state = NORMAL if self.modo_avanzado.get() else DISABLED
        for widget in self.adv_widgets:
            if isinstance(widget, ttk.Combobox):
                widget.config(state="readonly" if state == NORMAL else DISABLED)
            else:
                widget.config(state=state)
    
    def _select_excel(self):
        """Selecciona archivo Excel."""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[
                ("Archivos Excel", "*.xlsx *.xlsm *.xls"),
                ("Todos", "*.*")
            ]
        )
        
        if filename:
            self.archivo_excel.set(filename)
            self._load_sheets(filename)
    
    def _load_sheets(self, filepath):
        """Carga hojas del Excel."""
        self._log("Leyendo estructura del archivo...", "INFO")
        
        try:
            sheets = self.processor.get_sheet_names(filepath)
            self.hojas_disponibles = sheets
            
            # Configurar combos
            self.combo_datos['values'] = sheets
            self.combo_plantilla['values'] = sheets
            
            # Seleccionar DATA si existe
            if "DATA" in sheets:
                self.combo_datos.set("DATA")
            elif sheets:
                self.combo_datos.current(0)
            
            # Filtrar hojas de plantilla (FORM*)
            plantillas = [h for h in sheets if h.upper().startswith("FORM")]
            if plantillas:
                self.combo_plantilla.set(plantillas[0])
            elif sheets:
                self.combo_plantilla.current(0)
            
            self._log(f"Archivo cargado. {len(sheets)} hojas encontradas.", "SUCCESS")
            self.lbl_progress.config(text=f"Archivo listo: {Path(filepath).name}")
            
        except Exception as e:
            self._log(f"Error leyendo archivo: {e}", "ERROR")
    
    def _select_output_folder(self):
        """Selecciona carpeta de salida."""
        folder = filedialog.askdirectory()
        if folder:
            self.carpeta_salida.set(folder)
    
    def _log(self, msg: str, level: str = "INFO"):
        """Agrega mensaje al log."""
        self.log_text.insert(END, f"[{level}] {msg}\n", level)
        self.log_text.see(END)
    
    def _start_processing(self):
        """Inicia el procesamiento."""
        if self.is_processing:
            return
        
        if not self.archivo_excel.get():
            messagebox.showwarning("Falta archivo", "Seleccione un archivo Excel primero.")
            return
        
        if not self.carpeta_salida.get():
            messagebox.showwarning("Falta carpeta", "Seleccione carpeta de salida.")
            return
        
        # Crear carpeta si no existe
        Path(self.carpeta_salida.get()).mkdir(parents=True, exist_ok=True)
        
        self.is_processing = True
        self.btn_process.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.progress['value'] = 0
        
        # Iniciar en thread
        Thread(target=self._process_thread, daemon=True).start()
    
    def _stop_processing(self):
        """Detiene el procesamiento."""
        self.processor.stop()
        self._log("Solicitando detención...", "WARNING")
    
    def _process_thread(self):
        """Thread de procesamiento."""
        def progress_cb(idx, total, actual):
            percent = (idx / total) * 100
            self.after(0, lambda: self.progress.config(value=percent))
            self.after(0, lambda: self.lbl_progress.config(
                text=f"Procesando {idx}/{total}: {actual}"
            ))
            self.after(0, lambda: self._log(f"Procesando: {actual}", "INFO"))
        
        if self.modo_avanzado.get():
            # Modo COM
            config = {
                'archivo_excel': self.archivo_excel.get(),
                'hoja_plantilla': self.hoja_plantilla.get(),
                'hoja_datos': self.hoja_datos.get(),
                'columna_clave': self.columna_clave.get(),
                'generar_pdf': self.generar_pdf.get(),
                'carpeta_pdf': self.carpeta_salida.get(),
                'imprimir': self.imprimir.get(),
                'copias': self.copias.get()
            }
            stats = self.processor.process_with_com(config, progress_cb)
        else:
            # Modo simple
            stats = self.processor.process_simple(
                self.archivo_excel.get(),
                self.carpeta_salida.get(),
                self.columna_clave.get(),
                progress_cb
            )
        
        self.after(0, lambda: self._finish(stats))
    
    def _finish(self, stats):
        """Finaliza el proceso."""
        self.is_processing = False
        self.btn_process.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.progress['value'] = 0
        self.lbl_progress.config(text="Proceso finalizado")
        
        self._log(f"Procesados: {stats['procesados']}", "SUCCESS")
        self._log(f"Exitosos: {stats['exitosos']}", "SUCCESS")
        self._log(f"Fallidos: {stats['fallidos']}", "ERROR" if stats['fallidos'] > 0 else "SUCCESS")
        
        msg = (
            f"Proceso completado.\n\n"
            f"✅ Exitosos: {stats['exitosos']}\n"
            f"❌ Fallidos: {stats['fallidos']}"
        )
        
        if stats['fallidos'] > 0:
            messagebox.showwarning("Completado con errores", msg)
        else:
            messagebox.showinfo("Éxito", msg)
    
    def refresh(self):
        """Refresca el tab."""
        log.debug("Procesador Excel tab refrescado")
