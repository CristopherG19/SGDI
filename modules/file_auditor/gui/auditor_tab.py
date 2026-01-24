"""
SGDI - Tab Auditor de Archivos
================================

Interfaz para auditoría de archivos.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path

from modules.file_auditor.services.file_auditor import FileAuditor
from core.utils.logger import get_logger

log = get_logger(__name__)


class FileAuditorTab(ttk.Frame):
    """Tab para auditoría de archivos."""
    
    def __init__(self, parent):
        """Inicializa el tab."""
        super().__init__(parent, padding=20)
        
        self.auditor = FileAuditor()
        self.current_folder = None
        
        self._create_ui()
        log.debug("File Auditor tab inicializado")
    
    def _create_ui(self):
        """Crea la interfaz."""
        self.columnconfigure(0, weight=1)
        
        # Título
        ttk.Label(
            self,
            text="🔍 Auditor de Archivos",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        # Panel de lista de referencia
        self._create_reference_panel()
        
        # Botones
        self._create_action_panel()
        
        # Panel de resultados
        self._create_results_panel()
    
    def _create_reference_panel(self):
        """Panel de lista de referencia."""
        ref_frame = ttk.LabelFrame(
            self,
            text="📋 Lista de Referencia",
            padding=15
        )
        ref_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.rowconfigure(1, weight=1)
        
        ttk.Label(
            ref_frame,
            text="Pegar lista (Col 1: OC | Col 2: Número de Suministro):",
            font=("Segoe UI", 10)
        ).pack(anchor=W, pady=(0, 5))
        
        # Text area
        text_container = ttk.Frame(ref_frame)
        text_container.pack(fill=BOTH, expand=YES)
        
        scrollbar = ttk.Scrollbar(text_container)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.reference_text = tk.Text(
            text_container,
            height=10,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set
        )
        self.reference_text.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.config(command=self.reference_text.yview)
    
    def _create_action_panel(self):
        """Panel de botones."""
        action_frame = ttk.Frame(self)
        action_frame.grid(row=2, column=0, pady=15)
        
        ttk.Button(
            action_frame,
            text="🔍 Auditar Carpeta",
            command=self._audit_new,
            bootstyle="success",
            width=20
        ).pack(side=LEFT, padx=10)
        
        self.btn_rescan = ttk.Button(
            action_frame,
            text="🔄 Actualizar / Re-Scan",
            command=self._rescan,
            bootstyle="info",
            state=DISABLED,
            width=20
        )
        self.btn_rescan.pack(side=LEFT, padx=10)
    
    def _create_results_panel(self):
        """Panel de resultados."""
        results_frame = ttk.LabelFrame(
            self,
            text="📊 Informe de Resultados",
            padding=10
        )
        results_frame.grid(row=3, column=0, sticky="nsew")
        self.rowconfigure(3, weight=2)
        
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            height=15,
            font=("Consolas", 9),
            wrap=WORD,
            state=DISABLED
        )
        self.results_text.pack(fill=BOTH, expand=YES)
        
        # Tags para colores
        self.results_text.tag_config("HEADER", font=("Segoe UI", 12, "bold"), foreground="black")
        self.results_text.tag_config("NORMAL", foreground="#333333")
        self.results_text.tag_config("SUCCESS", foreground="#28a745", font=("Segoe UI", 11, "bold"))
        self.results_text.tag_config("ERROR", foreground="#dc3545", font=("Segoe UI", 11, "bold"))
        self.results_text.tag_config("WARNING", foreground="#d35400", font=("Segoe UI", 11, "bold"))
        self.results_text.tag_config("ERROR_TEXT", foreground="#dc3545")
        self.results_text.tag_config("WARNING_TEXT", foreground="#d35400")
        self.results_text.tag_config("TABLE_HEADER", font=("Consolas", 10, "bold"), background="#e9ecef")
    
    def _audit_new(self):
        """Inicia nueva auditoría."""
        # Validar lista
        text = self.reference_text.get("1.0", END).strip()
        if not text:
            messagebox.showwarning("Falta lista", "Ingrese la lista de referencia")
            return
        
        # Seleccionar carpeta
        folder = filedialog.askdirectory(title="Seleccionar carpeta a auditar")
        if not folder:
            return
        
        self.current_folder = folder
        self._perform_audit()
        self.btn_rescan.config(state=NORMAL)
    
    def _rescan(self):
        """Re-escanea carpeta actual."""
        if not self.current_folder:
            messagebox.showwarning("Sin carpeta", "Primero debe auditar una carpeta")
            return
        
        self._perform_audit()
    
    def _perform_audit(self):
        """Realiza la auditoría."""
        text = self.reference_text.get("1.0", END).strip()
        
        # Ejecutar auditoría
        results = self.auditor.audit(self.current_folder, text)
        
        # Mostrar resultados
        self.results_text.config(state=NORMAL)
        self.results_text.delete("1.0", END)
        
        # Encabezado
        self._insert("REPORTE DE VERIFICACIÓN\n", "HEADER")
        self._insert(f"Ruta: {results['folder_path']}\n", "NORMAL")
        self._insert(f"Fecha: {results['timestamp']}\n", "NORMAL")
        self._insert("-" * 100 + "\n\n", "NORMAL")
        
        # Estadísticas
        self._insert(f"Archivos esperados: {results['reference_count']}\n", "NORMAL")
        self._insert(f"Archivos encontrados: {results['found_count']}\n", "NORMAL")
        self._insert("\n", "NORMAL")
        
        # Sección faltantes
        missing = results['missing']
        if missing:
            self._insert(f"SECCIÓN 1: ARCHIVOS NO ENCONTRADOS ({len(missing)})\n", "ERROR")
            self._insert("Acción requerida: Buscar estos archivos y agregarlos a la carpeta.\n\n", "NORMAL")
            
            header = f"{'ORDEN (OC)':<20} | {'SUMINISTRO':<15} | {'OBSERVACIÓN / DETALLE'}\n"
            self._insert(header, "TABLE_HEADER")
            self._insert("-" * 100 + "\n", "NORMAL")
            
            for item in missing:
                line = f"{item['oc']:<20} | {item['supply']:<15} | {item['rest']}\n"
                self._insert(line, "ERROR_TEXT")
            
            self._insert("\n", "NORMAL")
        else:
            self._insert("[OK] LISTA COMPLETA: Todos los archivos de la lista están presentes.\n\n", "SUCCESS")
        
        # Sección extras
        extra = results['extra']
        if extra:
            self._insert(f"SECCIÓN 2: NO LISTADOS / POSIBLE ERROR DE DIGITACIÓN ({len(extra)})\n", "WARNING")
            self._insert("Estos archivos existen en la carpeta pero NO están en tu lista.\n\n", "NORMAL")
            
            header = f"{'NÚMERO DETECTADO':<25} | {'NOMBRE REAL DEL ARCHIVO'}\n"
            self._insert(header, "TABLE_HEADER")
            self._insert("-" * 100 + "\n", "NORMAL")
            
            for item in extra:
                line = f"{item['number']:<25} | {item['filename']}\n"
                self._insert(line, "WARNING_TEXT")
            
            self._insert("\n", "NORMAL")
        else:
            if not missing:
                self._insert("[OK] CARPETA LIMPIA: No hay archivos extraños.\n", "SUCCESS")
        
        self.results_text.config(state=DISABLED)
        
        # Mensaje final
        if not missing and not extra:
            messagebox.showinfo("Excelente", "✓ Todo cuadra perfectamente.")
        else:
            msg = f"Se encontraron discrepancias:\n\n"
            if missing:
                msg += f"❌ Faltantes: {len(missing)}\n"
            if extra:
                msg += f"⚠️ Extras: {len(extra)}\n"
            messagebox.showwarning("Atención", msg)
    
    def _insert(self, text: str, tag: str):
        """Inserta texto con tag."""
        self.results_text.insert(END, text, tag)
    
    def refresh(self):
        """Refresca el tab."""
        log.debug("File Auditor tab refrescado")
