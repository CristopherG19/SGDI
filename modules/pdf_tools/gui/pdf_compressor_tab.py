"""
SGDI - Tab Compresor de PDFs
=============================

Interfaz para comprimir archivos PDF.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path
from threading import Thread

from modules.pdf_tools.services.pdf_compressor import PDFCompressor
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


class PDFCompressorTab(ttk.Frame):
    """Tab para compresión de PDFs."""
    
    def __init__(self, parent):
        """Inicializa el tab."""
        super().__init__(parent, padding=20)
        
        self.compressor = PDFCompressor()
        self.is_processing = False
        
        # Variables
        self.folder_path = tk.StringVar()
        self.quality = tk.IntVar(value=70)
        
        self._create_ui()
        log.debug("PDF Compressor tab inicializado")
    
    def _create_ui(self):
        """Crea la interfaz."""
        self.columnconfigure(0, weight=1)
        
        # Título
        ttk.Label(
            self,
            text="📄 Compresor de PDFs",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        # Panel de configuración
        self._create_config_panel()
        
        # Info
        self._create_info_panel()
        
        # Botones
        self._create_action_panel()
        
        # Progreso
        self._create_progress_panel()
        
        # Resultados
        self._create_results_panel()
    
    def _create_config_panel(self):
        """Panel de configuración."""
        config_frame = ttk.LabelFrame(
            self,
            text="⚙️ Configuración",
            padding=15
        )
        config_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Carpeta
        ttk.Label(config_frame, text="Carpeta con PDFs:").grid(row=0, column=0, sticky=W, pady=5, padx=(0, 10))
        ttk.Entry(
            config_frame,
            textvariable=self.folder_path,
            font=("Segoe UI", 9)
        ).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(
            config_frame,
            text="Examinar",
            command=self._select_folder,
            bootstyle="info"
        ).grid(row=0, column=2)
        
        # Calidad
        ttk.Label(config_frame, text="Calidad JPEG:").grid(row=1, column=0, sticky=W, pady=5, padx=(0, 10))
        quality_frame = ttk.Frame(config_frame)
        quality_frame.grid(row=1, column=1, sticky="w")
        
        ttk.Scale(
            quality_frame,
            from_=10,
            to=100,
            variable=self.quality,
            orient=HORIZONTAL,
            length=200,
            command=lambda v: self.quality_label.config(text=f"{int(float(v))}%")
        ).pack(side=LEFT, padx=(0, 10))
        
        self.quality_label = ttk.Label(quality_frame, text="70%", font=("Segoe UI", 9, "bold"))
        self.quality_label.pack(side=LEFT)
        
        ttk.Label(
            config_frame,
            text="(Mayor calidad = menos compresión)",
            font=("Segoe UI", 8),
            bootstyle="secondary"
        ).grid(row=2, column=1, sticky=W, pady=(0, 5))
    
    def _create_info_panel(self):
        """Panel de información."""
        self.info_frame = ttk.LabelFrame(
            self,
            text="📊 Información",
            padding=15
        )
        self.info_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        self.info_label = ttk.Label(
            self.info_frame,
            text="Seleccione una carpeta para comenzar",
            font=("Segoe UI", 10),
            justify=LEFT
        )
        self.info_label.pack(anchor=W)
    
    def _create_action_panel(self):
        """Panel de botones."""
        action_frame = ttk.Frame(self)
        action_frame.grid(row=3, column=0, pady=15)
        
        self.btn_analyze = ttk.Button(
            action_frame,
            text="🔍 Analizar Carpeta",
            command=self._analyze,
            bootstyle="info",
            width=20
        )
        self.btn_analyze.pack(side=LEFT, padx=10)
        
        self.btn_compress = ttk.Button(
            action_frame,
            text="🚀 Comprimir PDFs",
            command=self._start_compression,
            bootstyle="success",
            state=DISABLED,
            width=20
        )
        self.btn_compress.pack(side=LEFT, padx=10)
        
        self.btn_stop = ttk.Button(
            action_frame,
            text="⏹️ Detener",
            command=self._stop_compression,
            bootstyle="danger",
            state=DISABLED,
            width=15
        )
        self.btn_stop.pack(side=LEFT, padx=10)
    
    def _create_progress_panel(self):
        """Panel de progreso."""
        progress_frame = ttk.Frame(self)
        progress_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            bootstyle="success-striped"
        )
        self.progress.grid(row=0, column=0, sticky="ew")
        
        self.lbl_progress = ttk.Label(
            progress_frame,
            text="Esperando...",
            font=("Segoe UI", 9)
        )
        self.lbl_progress.grid(row=1, column=0, sticky=W, pady=(5, 0))
    
    def _create_results_panel(self):
        """Panel de resultados."""
        results_frame = ttk.LabelFrame(
            self,
            text="📋 Resultados",
            padding=10
        )
        results_frame.grid(row=5, column=0, sticky="nsew")
        self.rowconfigure(5, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            height=10,
            font=("Consolas", 9),
            wrap=WORD
        )
        self.results_text.pack(fill=BOTH, expand=YES)
        
        # Tags
        self.results_text.tag_config("SUCCESS", foreground="#28a745")
        self.results_text.tag_config("ERROR", foreground="#dc3545")
        self.results_text.tag_config("INFO", foreground="#17a2b8")
        self.results_text.tag_config("SKIP", foreground="#ffc107")
    
    def _select_folder(self):
        """Selecciona carpeta."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            self.folder_path.set(folder)
            self.btn_analyze.config(state=NORMAL)
    
    def _log(self, msg: str, tag: str = "INFO"):
        """Agrega mensaje a resultados."""
        self.results_text.insert(END, f"{msg}\n", tag)
        self.results_text.see(END)
    
    def _analyze(self):
        """Analiza carpeta."""
        if not self.folder_path.get():
            messagebox.showwarning("Falta carpeta", "Seleccione una carpeta")
            return
        
        self.btn_analyze.config(state=DISABLED)
        self.results_text.delete("1.0", END)
        self._log("=== ANÁLISIS INICIAL ===", "INFO")
        self._log(f"Analizando: {self.folder_path.get()}", "INFO")
        
        Thread(target=self._analyze_thread, daemon=True).start()
    
    def _analyze_thread(self):
        """Thread de análisis."""
        analysis = self.compressor.analyze_folder(self.folder_path.get())
        self.after(0, lambda: self._show_analysis(analysis))
    
    def _show_analysis(self, analysis: dict):
        """Muestra resultados del análisis."""
        pdf_count = len(analysis['pdf_files'])
        size_mb = analysis['total_size'] / (1024 * 1024)
        folders = analysis['folder_count']
        
        self._log(f"\nCarpetas analizadas: {folders}", "INFO")
        self._log(f"Archivos PDF encontrados: {pdf_count}", "SUCCESS" if pdf_count > 0 else "ERROR")
        self._log(f"Tamaño total: {size_mb:.2f} MB", "INFO")
        
        self.info_label.config(
            text=f"Carpetas: {folders} | PDFs: {pdf_count} | Tamaño: {size_mb:.2f} MB"
        )
        
        self.btn_analyze.config(state=NORMAL)
        
        if pdf_count > 0:
            self.btn_compress.config(state=NORMAL)
            self._log("\n✓ Listo para comprimir", "SUCCESS")
        else:
            self._log("\n✗ No se encontraron archivos PDF", "ERROR")
    
    def _start_compression(self):
        """Inicia compresión."""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.btn_analyze.config(state=DISABLED)
        self.btn_compress.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        
        self.results_text.delete("1.0", END)
        self._log("=== INICIANDO COMPRESIÓN ===", "INFO")
        
        Thread(target=self._compress_thread, daemon=True).start()
    
    def _stop_compression(self):
        """Detiene compresión."""
        self.compressor.stop()
        self._log("\n⚠️ Deteniendo...", "INFO")
    
    def _compress_thread(self):
        """Thread de compresión."""
        def progress_cb(idx, total, filename, status):
            percent = (idx / total) * 100 if total > 0 else 0
            self.after(0, lambda: self.progress.config(value=percent))
            self.after(0, lambda: self.lbl_progress.config(text=f"{idx}/{total}: {filename}"))
            
            if "✓" in status:
                self.after(0, lambda: self._log(f"{status} - {filename}", "SUCCESS"))
            elif "✗" in status:
                self.after(0, lambda: self._log(f"{status} - {filename}", "ERROR"))
            elif "➡" in status:
                self.after(0, lambda: self._log(f"{status} - {filename}", "SKIP"))
        
        stats = self.compressor.compress_folder(
            self.folder_path.get(),
            self.quality.get(),
            progress_cb
        )
        
        self.after(0, lambda: self._finish_compression(stats))
    
    def _finish_compression(self, stats: dict):
        """Finaliza compresión."""
        self.is_processing = False
        self.btn_analyze.config(state=NORMAL)
        self.btn_compress.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.progress['value'] = 0
        self.lbl_progress.config(text="Completado")
        
        # Resumen
        saved_mb = stats['saved_bytes'] / (1024 * 1024)
        orig_mb = stats['original_bytes'] / (1024 * 1024)
        ratio = (stats['saved_bytes'] / stats['original_bytes'] * 100) if stats['original_bytes'] > 0 else 0
        
        self._log("\n=== RESUMEN FINAL ===", "INFO")
        self._log(f"Tiempo: {stats['duration']:.1f}s", "INFO")
        self._log(f"Archivos comprimidos: {stats['compressed']}", "SUCCESS")
        self._log(f"Sin cambios: {stats['skipped']}", "SKIP")
        self._log(f"Errores: {stats['errors']}", "ERROR" if stats['errors'] > 0 else "INFO")
        self._log(f"Espacio ahorrado: {saved_mb:.2f} MB", "SUCCESS")
        self._log(f"Tamaño original: {orig_mb:.2f} MB", "INFO")
        self._log(f"Reducción: {ratio:.1f}%", "SUCCESS")
        
        # Mensaje
        msg = (
            f"Compresión finalizada.\n\n"
            f"✅ Comprimidos: {stats['compressed']}\n"
            f"➡️ Sin cambios: {stats['skipped']}\n"
            f"❌ Errores: {stats['errors']}\n\n"
            f"💾 Espacio ahorrado: {saved_mb:.2f} MB ({ratio:.1f}%)"
        )
        
        if stats['compressed'] > 0:
            messagebox.showinfo("Completado", msg)
        else:
            messagebox.showinfo("Sin cambios", "No se realizaron compresiones.")
    
    def refresh(self):
        """Refresca el tab."""
        log.debug("PDF Compressor tab refrescado")
