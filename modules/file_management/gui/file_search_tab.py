"""
SGDI - Tab Buscador de Archivos
=================================

Interfaz para buscar y copiar archivos.
"""

import json
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path
from threading import Thread

from modules.file_management.services.file_searcher import FileSearcher
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


class FileSearchTab(ttk.Frame):
    """Tab para búsqueda y copia de archivos."""
    
    def __init__(self, parent):
        """Inicializa el tab."""
        super().__init__(parent, padding=20)
        
        self.searcher = FileSearcher()
        self.is_searching = False
        
        # Archivo de preferencias
        self.preferences_file = Settings.DATA_DIR / "config" / "file_search_preferences.json"
        self.preferences = self._load_preferences()
        
        # Variables con valores restaurados de preferencias
        self.source_path = tk.StringVar(value=self.preferences.get("last_source_path", ""))
        self.dest_path = tk.StringVar(value=self.preferences.get("last_dest_path", str(Settings.EXPORTS_DIR)))
        
        self._create_ui()
        log.debug("File Search tab inicializado")
    
    def _create_ui(self):
        """Crea la interfaz."""
        self.columnconfigure(0, weight=1)
        
        # Título
        ttk.Label(
            self,
            text="🔍 Buscador de Archivos",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        # Panel de configuración
        self._create_config_panel()
        
        # Panel de lista de archivos
        self._create_files_panel()
        
        # Botones de acción
        self._create_action_panel()
        
        # Progreso
        self._create_progress_panel()
        
        # Resultados
        self._create_results_panel()
    
    def _create_config_panel(self):
        """Panel de configuración."""
        config_frame = ttk.LabelFrame(
            self,
            text="📂 Configuración",
            padding=15
        )
        config_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Ruta origen
        ttk.Label(config_frame, text="Ruta de búsqueda:").grid(row=0, column=0, sticky=W, pady=5, padx=(0, 10))
        ttk.Entry(
            config_frame,
            textvariable=self.source_path,
            font=("Segoe UI", 9)
        ).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(
            config_frame,
            text="Examinar",
            command=self._select_source,
            bootstyle="info"
        ).grid(row=0, column=2)
        
        # Ruta destino
        ttk.Label(config_frame, text="Carpeta destino:").grid(row=1, column=0, sticky=W, pady=5, padx=(0, 10))
        ttk.Entry(
            config_frame,
            textvariable=self.dest_path,
            font=("Segoe UI", 9)
        ).grid(row=1, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(
            config_frame,
            text="Examinar",
            command=self._select_dest,
            bootstyle="info"
        ).grid(row=1, column=2)
    
    def _create_files_panel(self):
        """Panel de lista de archivos."""
        files_frame = ttk.LabelFrame(
            self,
            text="📄 Lista de Archivos a Buscar",
            padding=15
        )
        files_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.rowconfigure(2, weight=1)
        
        ttk.Label(
            files_frame,
            text="Pega la lista de archivos (uno por línea):",
            font=("Segoe UI", 9)
        ).pack(anchor=W, pady=(0, 5))
        
        # Text area
        text_container = ttk.Frame(files_frame)
        text_container.pack(fill=BOTH, expand=YES)
        
        scrollbar = ttk.Scrollbar(text_container)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.files_text = tk.Text(
            text_container,
            height=8,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set
        )
        self.files_text.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.config(command=self.files_text.yview)
        
        # Contador
        self.file_count_label = ttk.Label(
            files_frame,
            text="Archivos: 0",
            font=("Segoe UI", 9),
            bootstyle="info"
        )
        self.file_count_label.pack(anchor=E, pady=(5, 0))
        
        # Vincular evento
        self.files_text.bind('<KeyRelease>', self._update_file_count)
    
    def _create_action_panel(self):
        """Panel de botones."""
        action_frame = ttk.Frame(self)
        action_frame.grid(row=3, column=0, pady=15)
        
        self.btn_search = ttk.Button(
            action_frame,
            text="🔍 Buscar y Copiar",
            command=self._start_search,
            bootstyle="success",
            width=25
        )
        self.btn_search.pack(side=LEFT, padx=10)
        
        self.btn_stop = ttk.Button(
            action_frame,
            text="⏹️ Detener",
            command=self._stop_search,
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
            height=8,
            font=("Consolas", 9),
            state=DISABLED
        )
        self.results_text.pack(fill=BOTH, expand=YES)
        
        # Tags
        self.results_text.tag_config("SUCCESS", foreground="#28a745")
        self.results_text.tag_config("ERROR", foreground="#dc3545")
        self.results_text.tag_config("INFO", foreground="#17a2b8")
    
    def _load_preferences(self) -> dict:
        """Carga preferencias guardadas."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    log.debug(f"Preferencias cargadas: {prefs}")
                    return prefs
        except Exception as e:
            log.warning(f"No se pudieron cargar preferencias: {e}")
        
        # Valores por defecto
        return {
            "last_source_path": "",
            "last_dest_path": str(Settings.EXPORTS_DIR),
            "last_source_browse_dir": "",
            "last_dest_browse_dir": str(Settings.EXPORTS_DIR)
        }
    
    def _save_preferences(self):
        """Guarda preferencias."""
        try:
            self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
            log.debug(f"Preferencias guardadas: {self.preferences}")
        except Exception as e:
            log.warning(f"No se pudieron guardar preferencias: {e}")
    
    def _select_source(self):
        """Selecciona carpeta origen."""
        # Usar última ubicación de navegación para búsqueda (independiente)
        initial = self.preferences.get("last_source_browse_dir", "")
        
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta de búsqueda",
            initialdir=initial if initial and Path(initial).exists() else None
        )
        
        if folder:
            self.source_path.set(folder)
            # Guardar ruta seleccionada y directorio padre
            self.preferences["last_source_path"] = folder
            self.preferences["last_source_browse_dir"] = str(Path(folder).parent)
            self._save_preferences()
            log.info(f"Ruta de búsqueda actualizada: {folder}")
    
    def _select_dest(self):
        """Selecciona carpeta destino."""
        # Usar última ubicación de navegación para destino (independiente)
        initial = self.preferences.get("last_dest_browse_dir", str(Settings.EXPORTS_DIR))
        
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta destino",
            initialdir=initial if Path(initial).exists() else None
        )
        
        if folder:
            self.dest_path.set(folder)
            # Guardar ruta seleccionada y directorio padre
            self.preferences["last_dest_path"] = folder
            self.preferences["last_dest_browse_dir"] = str(Path(folder).parent)
            self._save_preferences()
            log.info(f"Ruta de destino actualizada: {folder}")
    
    def _update_file_count(self, event=None):
        """Actualiza contador de archivos."""
        text = self.files_text.get("1.0", END).strip()
        if text:
            files = [line.strip() for line in text.splitlines() if line.strip()]
            self.file_count_label.config(text=f"Archivos: {len(files)}")
        else:
            self.file_count_label.config(text="Archivos: 0")
    
    def _log(self, msg: str, tag: str = "INFO"):
        """Agrega mensaje a resultados."""
        self.results_text.config(state=NORMAL)
        self.results_text.insert(END, f"{msg}\n", tag)
        self.results_text.see(END)
        self.results_text.config(state=DISABLED)
    
    def _start_search(self):
        """Inicia la búsqueda."""
        if self.is_searching:
            return
        
        # Validar
        if not self.source_path.get():
            messagebox.showwarning("Falta ruta", "Ingrese la ruta de búsqueda")
            return
        
        if not self.dest_path.get():
            messagebox.showwarning("Falta destino", "Ingrese la carpeta destino")
            return
        
        text = self.files_text.get("1.0", END).strip()
        if not text:
            messagebox.showwarning("Falta lista", "Ingrese la lista de archivos")
            return
        
        # Preparar
        self.is_searching = True
        self.btn_search.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        
        self.results_text.config(state=NORMAL)
        self.results_text.delete("1.0", END)
        
        self.progress['value'] = 0
        
        # Iniciar thread
        Thread(target=self._search_thread, daemon=True).start()
    
    def _stop_search(self):
        """Detiene la búsqueda."""
        self.searcher.stop()
        self._log("⚠️ Deteniendo...", "INFO")
    
    def _search_thread(self):
        """Thread de búsqueda."""
        def progress_cb(current, total, msg):
            percent = (current / total) * 100 if total > 0 else 0
            self.after(0, lambda: self.progress.config(value=percent))
            self.after(0, lambda: self.lbl_progress.config(text=msg))
        
        # Obtener lista
        text = self.files_text.get("1.0", END).strip()
        file_names = [line.strip() for line in text.splitlines() if line.strip()]
        
        self._log(f"Iniciando búsqueda de {len(file_names)} archivos...", "INFO")
        self._log(f"Origen: {self.source_path.get()}", "INFO")
        self._log(f"Destino: {self.dest_path.get()}", "INFO")
        self._log("-" * 50, "INFO")
        
        # Buscar y copiar
        stats = self.searcher.search_and_copy(
            self.source_path.get(),
            file_names,
            self.dest_path.get(),
            progress_cb
        )
        
        self.after(0, lambda: self._finish_search(stats))
    
    def _finish_search(self, stats: dict):
        """Finaliza la búsqueda."""
        self.is_searching = False
        self.btn_search.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.progress['value'] = 0
        self.lbl_progress.config(text="Completado")
        
        # Mostrar resultados
        self._log("-" * 50, "INFO")
        self._log(f"✅ Archivos copiados: {stats['copied']}", "SUCCESS")
        self._log(f"❌ Errores: {stats['errors']}", "ERROR" if stats['errors'] > 0 else "INFO")
        
        # Mostrar duplicados encontrados
        if stats.get('duplicate_files'):
            self._log("\n" + "=" * 50, "INFO")
            self._log(f"⚠️ Archivos Duplicados Encontrados: {len(stats['duplicate_files'])}", "INFO")
            self._log("=" * 50, "INFO")
            for file_name, count in stats['duplicate_files'].items():
                self._log(f"  📄 {file_name}: encontrado {count} veces", "INFO")
                self._log(f"     → Se copiaron todas las versiones con sufijo '_copia#'", "INFO")
        
        # Mostrar detalles de errores
        if stats.get('error_details'):
            self._log("\n" + "=" * 50, "ERROR")
            self._log(f"❌ DETALLES DE ERRORES ({len(stats['error_details'])})", "ERROR")
            self._log("=" * 50, "ERROR")
            
            for idx, error in enumerate(stats['error_details'], 1):
                self._log(f"\n  Error #{idx}:", "ERROR")
                self._log(f"  📄 Archivo: {error['file_name']}", "INFO")
                self._log(f"  🔍 Búsqueda: {error['search_name']}", "INFO")
                self._log(f"  ⚠️ Tipo: {error['error_type']}", "ERROR")
                self._log(f"  💬 Mensaje: {error['error_message']}", "ERROR")
                self._log(f"  📂 Origen: {error['source_path']}", "INFO")
                self._log(f"  📁 Destino: {error['destination_path']}", "INFO")
                self._log(f"  🕒 Hora: {error['timestamp']}", "INFO")
                
                # Sugerencias según tipo de error
                error_type = error['error_type']
                if error_type == "FileExistsError":
                    self._log("  💡 Sugerencia: El archivo ya existe en destino. Verifique duplicados.", "INFO")
                elif error_type == "PermissionError":
                    self._log("  💡 Sugerencia: Sin permisos. Ejecute como administrador o cambie permisos.", "INFO")
                elif error_type == "FileNotFoundError":
                    self._log("  💡 Sugerencia: El archivo fue movido/eliminado durante la copia.", "INFO")
                elif "WinError 5" in error['error_message']:
                    self._log("  💡 Sugerencia: Acceso denegado. Cierre el archivo si está abierto.", "INFO")
        
        # Mostrar archivos no encontrados
        if stats['not_found']:
            self._log(f"\n⚠️ No encontrados ({len(stats['not_found'])}):", "INFO")
            for name in stats['not_found'][:10]:
                self._log(f"  - {name}", "ERROR")
            if len(stats['not_found']) > 10:
                self._log(f"  ... y {len(stats['not_found']) - 10} más", "INFO")
        
        # Resumen final
        self._log("\n" + "=" * 50, "INFO")
        self._log("📊 RESUMEN FINAL", "INFO")
        self._log("=" * 50, "INFO")
        self._log(f"✅ Archivos copiados exitosamente: {stats['copied']}", "SUCCESS")
        self._log(f"❌ Errores durante la copia: {stats['errors']}", "ERROR" if stats['errors'] > 0 else "INFO")
        self._log(f"⚠️ Archivos no encontrados: {len(stats['not_found'])}", "INFO")
        self._log(f"🔄 Archivos con duplicados: {len(stats.get('duplicate_files', {}))}", "INFO")
        
        # Mensaje final
        msg = (
            f"Proceso completado.\n\n"
            f"✅ Copiados: {stats['copied']}\n"
            f"❌ Errores: {stats['errors']}\n"
            f"⚠️ No encontrados: {len(stats['not_found'])}\n"
            f"🔄 Duplicados: {len(stats.get('duplicate_files', {}))}"
        )
        
        if stats['errors'] > 0:
            msg += "\n\n💡 Revise los DETALLES DE ERRORES arriba para más información."
            messagebox.showwarning("Completado con errores", msg)
        else:
            messagebox.showinfo("Éxito", msg)

    
    def refresh(self):
        """Refresca el tab."""
        log.debug("File Search tab refrescado")
