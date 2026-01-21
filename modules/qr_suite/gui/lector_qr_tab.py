"""
SGDI - Tab Lector de QR
========================

Interfaz gráfica para lectura y renombrado automático de archivos con códigos QR.

Este módulo proporciona un tab GUI que permite procesar directorios completos
de archivos PDF e imágenes, leer sus códigos QR, y renombrarlos automáticamente
basados en el contenido del QR. Incluye procesamiento por lotes con progreso
en tiempo real y gestión inteligente de duplicados.

Features:
    - Procesamiento batch de PDFs e imágenes
    - Renombrado automático basado en contenido QR
    - Organización: archivos procesados vs. sin QR
    - Políticas de duplicados configurables
    - Progreso en tiempo real con logs detallados
    - Estadísticas de procesamiento
    - Botón de detención para control manual

UI Components:
    - Panel de configuración: carpetas de entrada/salida/error
    - Panel de control: opciones de duplicados, botones de acción
    - Panel de logs: seguimiento en tiempo real del procesamiento

Author:
    SGDI Development Team

Version:
    1.0.0
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, scrolledtext
from pathlib import Path
from threading import Thread

from modules.qr_suite.services.qr_reader import QRReader
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


class LectorQRTab(ttk.Frame):
    """Tab GUI para lectura de QR y renombrado automático de archivos.
    
    Proporciona una interfaz completa para procesar directorios de archivos
    (PDFs e imágenes), leer sus códigos QR, renombrarlos automáticamente usando
    el contenido del QR, y organizarlos en carpetas separadas según tengan o
    no código QR. Incluye logs en tiempo real y estadísticas de procesamiento.
    
    Attributes:
        reader (QRReader): Instancia del servicio lector de QR
        is_processing (bool): Bandera indicando si hay un proceso en curso
        folder_input (tk.StringVar): Variable para carpeta de entrada
        folder_output (tk.StringVar): Variable para carpeta de procesados
        folder_error (tk.StringVar): Variable para carpeta de errores
        use_poppler (tk.BooleanVar): Si usar poppler para PDFs
        poppler_path (tk.StringVar): Ruta a poppler en Windows
        duplicate_policy (tk.StringVar): Política de duplicados
        stats (dict): Estadísticas del último procesamiento
    
    Example:
        >>> from tkinter import Tk
        >>> root = Tk()
        >>> tab = LectorQRTab(root)
        >>> tab.pack()
    
    Note:
        - Los archivos sin QR se mueven a folder_error
        - Los archivos exitosos se renombran y mueven a folder_output
        - El procesamiento se ejecuta en un thread separado para no bloquear UI
    """
    
    def __init__(self, parent):
        """Inicializa el tab lector de QR con todos sus componentes.
        
        Configura las variables de control, instancia el servicio lector,
        y construye la interfaz gráfica completa con paneles de configuración,
        control y logs.
        
        Args:
            parent (tk.Widget): Widget padre (generalmente un Notebook o Frame).
        """
        super().__init__(parent, padding=20)
        
        self.reader = QRReader()
        self.processing = False
        
        # Variables
        self.input_folder = tk.StringVar(value=str(Settings.DATA_DIR / "qr_input"))
        self.output_folder = tk.StringVar(value=str(Settings.DATA_DIR / "qr_renamed"))
        self.error_folder = tk.StringVar(value=str(Settings.DATA_DIR / "qr_no_qr"))
        self.poppler_path = tk.StringVar(value=r"C:\poppler\Library\bin")
        self.duplicate_policy = tk.StringVar(value="renombrar")
        
        # Stats
        self.stats = {
            'procesados': 0,
            'exitosos': 0,
            'sin_qr': 0,
            'saltados': 0,
            'fallidos': 0
        }
        
        self._create_ui()
        log.debug("Lector QR tab inicializado")
    
    def _create_ui(self):
        """Crea la interfaz."""
        # Grid principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        # Título
        ttk.Label(
            self,
            text="📖 Lector y Renombrador QR",
            font=("Segoe UI", 20, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=0, sticky=W, pady=(0, 20))
        
        # Panel de configuración
        self._create_config_panel()
        
        # Panel de control
        self._create_control_panel()
        
        # Panel de logs
        self._create_log_panel()
    
    def _create_config_panel(self):
        """Crea panel de configuración."""
        config_frame = ttk.LabelFrame(
            self,
            text="Configuración de Carpetas",
            padding=15
        )
        config_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        config_frame.columnconfigure(1, weight=1)
        
        # Carpeta de entrada
        self._create_folder_selector(
            config_frame, "Entrada:", self.input_folder, 0,
            "Carpeta con archivos a procesar"
        )
        
        # Carpeta de salida
        self._create_folder_selector(
            config_frame, "Salida:", self.output_folder, 1,
            "Carpeta para archivos renombrados"
        )
        
        # Carpeta de error
        self._create_folder_selector(
            config_frame, "Sin QR:", self.error_folder, 2,
            "Carpeta para archivos sin código QR"
        )
        
        # Poppler (para PDFs)
        self._create_folder_selector(
            config_frame, "Poppler:", self.poppler_path, 3,
            "Ruta a Poppler (solo para PDFs)"
        )
        
        # Política de duplicados
        ttk.Label(
            config_frame,
            text="Duplicados:",
            font=("Segoe UI", 10)
        ).grid(row=4, column=0, sticky=W, pady=5)
        
        policy_frame = ttk.Frame(config_frame)
        policy_frame.grid(row=4, column=1, columnspan=2, sticky=W, pady=5)
        
        policies = [
            ("Renombrar (sufijo)", "renombrar"),
            ("Sobrescribir", "sobrescribir"),
            ("Saltar", "saltar"),
            ("Comparar (MD5)", "comparar")
        ]
        
        for text, value in policies:
            ttk.Radiobutton(
                policy_frame,
                text=text,
                variable=self.duplicate_policy,
                value=value,
                bootstyle="primary"
            ).pack(side=LEFT, padx=10)
    
    def _create_folder_selector(self, parent, label, variable, row, tooltip=""):
        """Crea selector de carpeta."""
        ttk.Label(
            parent,
            text=label,
            font=("Segoe UI", 10)
        ).grid(row=row, column=0, sticky=W, pady=5)
        
        entry = ttk.Entry(
            parent,
            textvariable=variable,
            font=("Segoe UI", 9)
        )
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Button(
            parent,
            text="📁",
            command=lambda: self._select_folder(variable),
            width=3,
            bootstyle="secondary-outline"
        ).grid(row=row, column=2, pady=5)
    
    def _select_folder(self, variable):
        """Abre diálogo de selección de carpeta."""
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta",
            initialdir=variable.get()
        )
        if folder:
            variable.set(folder)
    
    def _create_control_panel(self):
        """Crea panel de control."""
        control_frame = ttk.Frame(self)
        control_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        
        # Botones
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=X, pady=(0, 10))
        
        self.btn_start = ttk.Button(
            btn_frame,
            text="▶️ Iniciar Procesamiento",
            command=self._start_processing,
            bootstyle="success",
            width=25
        )
        self.btn_start.pack(side=LEFT, padx=5)
        
        self.btn_stop = ttk.Button(
            btn_frame,
            text="⏹️ Detener",
            command=self._stop_processing,
            bootstyle="danger",
            state=DISABLED,
            width=15
        )
        self.btn_stop.pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="🗑️ Limpiar Log",
            command=self._clear_log,
            bootstyle="secondary-outline",
            width=15
        ).pack(side=LEFT, padx=5)
        
        # Estadísticas
        stats_frame = ttk.LabelFrame(control_frame, text="Estadísticas", padding=10)
        stats_frame.pack(fill=X, pady=(0, 10))
        
        self.stats_label = ttk.Label(
            stats_frame,
            text=self._format_stats(),
            font=("Segoe UI", 10, "bold"),
            bootstyle="info"
        )
        self.stats_label.pack()
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            control_frame,
            mode='determinate',
            bootstyle="success-striped"
        )
        self.progress.pack(fill=X, pady=(0, 5))
        
        self.progress_label = ttk.Label(
            control_frame,
            text="Listo para procesar",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        )
        self.progress_label.pack(anchor=W)
    
    def _create_log_panel(self):
        """Crea panel de logs."""
        log_frame = ttk.LabelFrame(self, text="Log de Procesamiento", padding=10)
        log_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 0))
        self.rowconfigure(3, weight=1)
        
        # Crear ScrolledText
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=("Consolas", 9),
            wrap=WORD
        )
        self.log_text.pack(fill=BOTH, expand=YES)
        
        # Tags para colores
        self.log_text.tag_config("INFO", foreground="#3498db")
        self.log_text.tag_config("SUCCESS", foreground="#27ae60")
        self.log_text.tag_config("WARNING", foreground="#f39c12")
        self.log_text.tag_config("ERROR", foreground="#e74c3c")
    
    def _format_stats(self):
        """Formatea estadísticas para mostrar."""
        return (
            f"Procesados: {self.stats['procesados']} | "
            f"Exitosos: {self.stats['exitosos']} | "
            f"Sin QR: {self.stats['sin_qr']} | "
            f"Saltados: {self.stats['saltados']} | "
            f"Fallidos: {self.stats['fallidos']}"
        )
    
    def _log(self, message, level="INFO"):
        """Agrega mensaje al log."""
        self.log_text.insert(tk.END, f"[{level}] {message}\n", level)
        self.log_text.see(tk.END)
    
    def _clear_log(self):
        """Limpia el log."""
        self.log_text.delete(1.0, tk.END)
        self.stats = {k: 0 for k in self.stats}
        self.stats_label.config(text=self._format_stats())
    
    def _start_processing(self):
        """Inicia el procesamiento."""
        if self.processing:
            return
        
        # Validar carpetas
        input_path = Path(self.input_folder.get())
        if not input_path.exists():
            self._log(f"Carpeta de entrada no existe: {input_path}", "ERROR")
            return
        
        # Cambiar estado UI
        self.processing = True
        self.btn_start.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self._clear_log()
        
        self._log(f"Iniciando procesamiento desde: {input_path}", "INFO")
        
        # Iniciar thread
        thread = Thread(target=self._process_thread, daemon=True)
        thread.start()
    
    def _stop_processing(self):
        """Detiene el procesamiento."""
        self.reader.stop()
        self._log("Deteniendo procesamiento...", "WARNING")
        self.btn_stop.config(state=DISABLED)
    
    def _process_thread(self):
        """Thread de procesamiento."""
        def progress_callback(idx, total, filename, result):
            # Actualizar UI desde thread
            self.after(0, lambda: self._update_progress(idx, total, filename, result))
        
        # Procesar directorio
        final_stats = self.reader.process_directory(
            input_folder=self.input_folder.get(),
            output_folder=self.output_folder.get(),
            error_folder=self.error_folder.get(),
            poppler_path=self.poppler_path.get() if self.poppler_path.get() else None,
            duplicate_policy=self.duplicate_policy.get(),
            progress_callback=progress_callback
        )
        
        # Finalizar
        self.after(0, lambda: self._finish_processing(final_stats))
    
    def _update_progress(self, idx, total, filename, result):
        """Actualiza progreso en UI."""
        # Actualizar barra
        progress_pct = (idx / total) * 100
        self.progress['value'] = progress_pct
        
        # Actualizar label
        self.progress_label.config(
            text=f"Procesando {idx}/{total}: {filename}"
        )
        
        # Actualizar stats
        self.stats['procesados'] += 1
        
        if result['action'] == 'renamed_and_moved':
            self.stats['exitosos'] += 1
            self._log(f"✓ {filename} → {Path(result['final_path']).name}", "SUCCESS")
        elif result['action'] == 'moved_to_error':
            self.stats['sin_qr'] += 1
            self._log(f"⚠ {filename}: {result['message']}", "WARNING")
        elif result['action'] == 'skipped':
            self.stats['saltados'] += 1
            self._log(f"○ {filename}: Saltado (duplicado)", "INFO")
        else:
            self.stats['fallidos'] += 1
            self._log(f"✗ {filename}: {result['message']}", "ERROR")
        
        self.stats_label.config(text=self._format_stats())
    
    def _finish_processing(self, final_stats):
        """Finaliza el procesamiento."""
        self.processing = False
        self.btn_start.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.progress['value'] = 0
        self.progress_label.config(text="Procesamiento completado")
        
        # Mensaje final
        if final_stats['fallidos'] == 0 and final_stats['procesados'] > 0:
            self._log("✅ Proceso completado exitosamente", "SUCCESS")
        elif final_stats['procesados'] == 0:
            self._log("No se encontraron archivos para procesar", "WARNING")
        else:
            self._log("Proceso finalizado con observaciones", "INFO")
        
        log.info(f"Procesamiento completado: {final_stats}")
    
    def refresh(self):
        """Refresca el tab."""
        log.debug("Lector QR tab refrescado")
