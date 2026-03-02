"""
SGDI - Dropbox URL Extractor Tab
=================================

Interfaz gráfica para extraer URLs de archivos en Dropbox.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from pathlib import Path
from threading import Thread
from datetime import datetime, date
from typing import Dict, List, Optional
import os

from modules.dropbox_extractor.services.dropbox_client import DropboxClient
from modules.dropbox_extractor.services.url_extractor import URLExtractor
from modules.dropbox_extractor.services.export_service import ExportService
from core.database.simple_db import get_db
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


class DropboxExtractorTab(ttk.Frame):
    """Tab para extracción de URLs de Dropbox."""
    
    def __init__(self, parent):
        """Inicializa el tab."""
        super().__init__(parent, padding=20)
        
        # Servicios
        self.dbx_client = None
        self.extractor = None
        self.export_service = ExportService()
        self.db = get_db()
        
        #Estado
        self.is_extracting = False
        self.results = []
        self.url_cache = {}  # Cache de URLs
        
        # Variables
        self.connection_status = tk.StringVar(value="Desconectado")
        self.folder_inicial = tk.BooleanVar(value=True)
        self.folder_posterior = tk.BooleanVar(value=True)
        self.folder_pattern = tk.StringVar()
        self.date_from = tk.StringVar()
        self.date_to = tk.StringVar()
        self.root_path = tk.StringVar(value=os.getenv('DROPBOX_ROOT_FOLDER', '/INACAL'))
        self.template_var = tk.StringVar(value="standard")
        
        # OAuth credentials
        self.refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN', '')
        self.app_key = os.getenv('DROPBOX_APP_KEY', '')
        self.app_secret = os.getenv('DROPBOX_APP_SECRET', '')
        
        # Crear UI
        self._create_ui()
        
        # Auto-conectar si hay credenciales
        if self.refresh_token and self.app_key and self.app_secret:
            if (self.refresh_token != 'your_refresh_token_here' and 
                self.app_key != 'your_app_key_here'):
                self.after(100, self._auto_connect)
    
    def _create_ui(self):
        """Crea la interfaz."""
        # Panel principal con scroll
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Crear paneles
        self._create_connection_panel(main_frame)
        self._create_filters_panel(main_frame)
        self._create_action_panel(main_frame)
        self._create_progress_panel(main_frame)
        self._create_results_panel(main_frame)
    
    def _create_connection_panel(self, parent):
        """Panel de conexión."""
        frame = ttk.LabelFrame(parent, text="Conexión a Dropbox (OAuth 2.0)", padding=15)
        frame.pack(fill=X, pady=(0, 10))
        
        # Row 1: Estado y botón conectar
        row1 = ttk.Frame(frame)
        row1.pack(fill=X, pady=5)
        
        ttk.Label(row1, text="Estado:", width=15).pack(side=LEFT)
        status_label = ttk.Label(
            row1,
            textvariable=self.connection_status,
            font=('Segoe UI', 10, 'bold')
        )
        status_label.pack(side=LEFT, padx=(10, 20))
        
        btn_connect = ttk.Button(
            row1,
            text="🔄 Reconectar",
            command=self._connect_dropbox,
            bootstyle=PRIMARY,
            width=15
        )
        btn_connect.pack(side=LEFT, padx=5)
        
        # Row 2: Configuración
        row2 = ttk.Frame(frame)
        row2.pack(fill=X, pady=5)
        
        ttk.Label(row2, text="Carpeta Raíz:", width=15).pack(side=LEFT)
        ttk.Entry(row2, textvariable=self.root_path, width=30).pack(side=LEFT, padx=10)
        
        # Info sobre configuración
        ttk.Label(
            row2,
            text="💡 Credenciales OAuth configuradas en .env",
            foreground='gray',
            font=('Segoe UI', 9)
        ).pack(side=LEFT, padx=(20, 0))
    
    def _create_filters_panel(self, parent):
        """Panel de filtros."""
        frame = ttk.LabelFrame(parent, text="Filtros de Extracción", padding=15)
        frame.pack(fill=X, pady=(0, 10))
        
        # Row 1: Checkboxes de tipo de carpeta
        row1 = ttk.Frame(frame)
        row1.pack(fill=X, pady=5)
        
        ttk.Label(row1, text="Tipo de Verificación:", width=18).pack(side=LEFT)
        
        chk_inicial = ttk.Checkbutton(
            row1,
            text="Verificación Inicial",
            variable=self.folder_inicial,
            bootstyle="success-round-toggle"
        )
        chk_inicial.pack(side=LEFT, padx=10)
        
        chk_posterior = ttk.Checkbutton(
            row1,
            text="Verificación Posterior",
            variable=self.folder_posterior,
            bootstyle="info-round-toggle"
        )
        chk_posterior.pack(side=LEFT, padx=10)
        
        # Row 2: Fechas
        row2 = ttk.Frame(frame)
        row2.pack(fill=X, pady=5)
        
        ttk.Label(row2, text="Rango de Fechas:", width=18).pack(side=LEFT)
        ttk.Label(row2, text="Desde:").pack(side=LEFT, padx=(10, 5))
        ttk.Entry(row2, textvariable=self.date_from, width=15).pack(side=LEFT, padx=5)
        ttk.Label(row2, text="(YYYY-MM-DD)", foreground='gray').pack(side=LEFT, padx=5)
        
        ttk.Label(row2, text="Hasta:").pack(side=LEFT, padx=(20, 5))
        ttk.Entry(row2, textvariable=self.date_to, width=15).pack(side=LEFT, padx=5)
        ttk.Label(row2, text="(YYYY-MM-DD)", foreground='gray').pack(side=LEFT, padx=5)
        
        # Row 3: Patrón de carpeta
        row3 = ttk.Frame(frame)
        row3.pack(fill=X, pady=5)
        
        ttk.Label(row3, text="Patrón de Carpeta:", width=18).pack(side=LEFT)
        ttk.Entry(row3, textvariable=self.folder_pattern, width=30).pack(side=LEFT, padx=10)
        ttk.Label(row3, text="Ej: 2025 (búsqueda en nombres de carpetas)", foreground='gray').pack(side=LEFT, padx=5)
    
    def _create_action_panel(self, parent):
        """Panel de acciones."""
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=(0, 10))
        
        btn_preview = ttk.Button(
            frame,
            text="🔍 Vista Previa de Carpetas",
            command=self._preview_folders,
            bootstyle=INFO,
            width=25
        )
        btn_preview.pack(side=LEFT, padx=5)
        
        btn_extract = ttk.Button(
            frame,
            text="⚡ Extraer URLs",
            command=self._start_extraction,
            bootstyle=SUCCESS,
            width=20
        )
        btn_extract.pack(side=LEFT, padx=5)
        
        btn_stop = ttk.Button(
            frame,
            text="⏹ Detener",
            command=self._stop_extraction,
            bootstyle=DANGER,
            width=15
        )
        btn_stop.pack(side=LEFT, padx=5)
        
        btn_export = ttk.Button(
            frame,
            text="📊 Exportar Excel",
            command=self._export_results,
            bootstyle=WARNING,
            width=20
        )
        btn_export.pack(side=LEFT, padx=5)
        
        btn_save_db = ttk.Button(
            frame,
            text="💾 Guardar en BD",
            command=self._save_to_db,
            bootstyle=SECONDARY,
            width=18
        )
        btn_save_db.pack(side=LEFT, padx=5)
    
    def _create_progress_panel(self, parent):
        """Panel de progreso."""
        frame = ttk.LabelFrame(parent, text="Progreso", padding=15)
        frame.pack(fill=X, pady=(0, 10))
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            frame,
            mode='determinate',
            bootstyle=SUCCESS
        )
        self.progress_bar.pack(fill=X, pady=(0, 10))
        
        # Información de progreso
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=X)
        
        self.progress_label = ttk.Label(
            info_frame,
            text="Listo para iniciar...",
            font=('Segoe UI', 10)
        )
        self.progress_label.pack(side=LEFT)
        
        self.stats_label = ttk.Label(
            info_frame,
            text="",
            font=('Segoe UI', 9),
            foreground='gray'
        )
        self.stats_label.pack(side=RIGHT)
        
        # Log de actividad
        log_label = ttk.Label(frame, text="Log de Actividad:")
        log_label.pack(anchor=W, pady=(10, 5))
        
        log_frame = ttk.Frame(frame)
        log_frame.pack(fill=BOTH, expand=YES)
        
        self.log_text = tk.Text(
            log_frame,
            height=6,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=YES)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def _create_results_panel(self, parent):
        """Panel de resultados."""
        frame = ttk.LabelFrame(parent, text="Resultados", padding=15)
        frame.pack(fill=BOTH, expand=YES)
        
        # Toolbar de resultados
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=X, pady=(0, 10))
        
        self.results_count_label = ttk.Label(
            toolbar,
            text="0 URLs extraídas",
            font=('Segoe UI', 10, 'bold')
        )
        self.results_count_label.pack(side=LEFT)
        
        # Selector de plantilla
        ttk.Label(toolbar, text="Plantilla:").pack(side=RIGHT, padx=(0, 5))
        template_combo = ttk.Combobox(
            toolbar,
            textvariable=self.template_var,
            values=['standard', 'detailed', 'simple'],
            state='readonly',
            width=15
        )
        template_combo.pack(side=RIGHT, padx=5)
        
        # Tabla de resultados
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=BOTH, expand=YES)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side=RIGHT, fill=Y)
        
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side=BOTTOM, fill=X)
        
        # Treeview
        columns = ('nombre', 'carpeta', 'tipo', 'tamaño', 'modificado')
        self.results_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='tree headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode='extended'
        )
        
        vsb.config(command=self.results_tree.yview)
        hsb.config(command=self.results_tree.xview)
        
        # Configurar columnas
        self.results_tree.heading('#0', text='#')
        self.results_tree.column('#0', width=50, stretch=NO)
        
        self.results_tree.heading('nombre', text='Nombre Archivo')
        self.results_tree.column('nombre', width=300)
        
        self.results_tree.heading('carpeta', text='Carpeta')
        self.results_tree.column('carpeta', width=250)
        
        self.results_tree.heading('tipo', text='Tipo')
        self.results_tree.column('tipo', width=100)
        
        self.results_tree.heading('tamaño', text='Tamaño')
        self.results_tree.column('tamaño', width=100)
        
        self.results_tree.heading('modificado', text='Modificado')
        self.results_tree.column('modificado', width=150)
        
        self.results_tree.pack(fill=BOTH, expand=YES)
        
        # Menú contextual
        self.context_menu = tk.Menu(self.results_tree, tearoff=0)
        self.context_menu.add_command(label="Copiar URL", command=self._copy_url)
        self.context_menu.add_command(label="Abrir URL", command=self._open_url)
        self.results_tree.bind("<Button-3>", self._show_context_menu)
    
    # ===================================
    # Métodos de conexión
    # ===================================
    
    def _auto_connect(self):
        """Auto-conecta al iniciar si hay credenciales."""
        self._log("Auto-conectando a Dropbox...", "INFO")
        self._connect_dropbox()
    
    def _connect_dropbox(self):
        """Conecta a Dropbox usando OAuth 2.0."""
        # Validar que hay credenciales
        if not self.refresh_token or not self.app_key or not self.app_secret:
            messagebox.showerror(
                "Error de Configuración",
                "Faltan credenciales de Dropbox en el archivo .env\n\n"
                "Asegúrate de configurar:\n"
                "- DROPBOX_REFRESH_TOKEN\n"
                "- DROPBOX_APP_KEY\n"
                "- DROPBOX_APP_SECRET"
            )
            return
        
        self._log("Conectando a Dropbox con OAuth 2.0...", "INFO")
        
        try:
            # Crear cliente con OAuth credentials
            self.dbx_client = DropboxClient(
                self.refresh_token,
                self.app_key,
                self.app_secret
            )
            
            if self.dbx_client.connect():
                self.extractor = URLExtractor(self.dbx_client)
                self.connection_status.set("✅ Conectado")
                self._log("Conexión exitosa a Dropbox", "SUCCESS")
                
                # Cargar cache desde DB
                self._load_url_cache()
            else:
                self.connection_status.set("❌ Error de Conexión")
                self._log("Error al conectar. Verifica credenciales en .env", "ERROR")
                
        except Exception as e:
            self.connection_status.set("❌ Error")
            self._log(f"Error: {str(e)}", "ERROR")
            log.error(f"Error al conectar a Dropbox: {e}")
    
    def _load_url_cache(self):
        """Carga URLs desde la base de datos al cache."""
        try:
            urls = self.db.get_dropbox_urls()
            self.url_cache = {item['file_path']: item['shared_url'] for item in urls}
            self._log(f"Cache cargado: {len(self.url_cache)} URLs en memoria", "INFO")
        except Exception as e:
            log.error(f"Error al cargar cache: {e}")
    
    # ===================================
    # Métodos de extracción
    # ===================================
    
    def _preview_folders(self):
        """Muestra vista previa de carpetas."""
        if not self.dbx_client or not self.dbx_client.is_connected():
            messagebox.showwarning("Advertencia", "Conecta a Dropbox primero")
            return
        
        self._log("Obteniendo estructura de carpetas...", "INFO")
        
        try:
            root = self.root_path.get().strip()
            folders = self.dbx_client.list_folders(root)
            
            # Mostrar en diálogo
            dialog = tk.Toplevel(self)
            dialog.title("Vista Previa de Carpetas")
            dialog.geometry("600x400")
            
            ttk.Label(
                dialog,
                text=f"Carpetas encontradas en: {root}",
                font=('Segoe UI', 11, 'bold')
            ).pack(pady=10)
            
            # Lista
            list_frame = ttk.Frame(dialog)
            list_frame.pack(fill=BOTH, expand=YES, padx=20, pady=10)
            
            listbox = tk.Listbox(list_frame, font=('Segoe UI', 10))
            listbox.pack(side=LEFT, fill=BOTH, expand=YES)
            
            scrollbar = ttk.Scrollbar(list_frame, command=listbox.yview)
            scrollbar.pack(side=RIGHT, fill=Y)
            listbox.config(yscrollcommand=scrollbar.set)
            
            for folder in folders:
                listbox.insert(tk.END, folder['name'])
            
            ttk.Label(
                dialog,
                text=f"Total: {len(folders)} carpetas",
                font=('Segoe UI', 10)
            ).pack(pady=10)
            
            ttk.Button(
                dialog,
                text="Cerrar",
                command=dialog.destroy,
                bootstyle=SECONDARY
            ).pack(pady=10)
            
            self._log(f"Encontradas {len(folders)} carpetas", "SUCCESS")
            
        except Exception as e:
            self._log(f"Error al obtener carpetas: {str(e)}", "ERROR")
            log.error(f"Error en preview: {e}")
    
    def _start_extraction(self):
        """Inicia la extracción de URLs."""
        if not self.dbx_client or not self.dbx_client.is_connected():
            messagebox.showwarning("Advertencia", "Conecta a Dropbox primero")
            return
        
        if self.is_extracting:
            messagebox.showinfo("Info", "Ya hay una extracción en curso")
            return
        
        # Validar filtros
        config = self._build_config()
        if not config:
            return
        
        # Confirmar
        folder_types = config.get('folder_types', [])
        msg = f"¿Iniciar extracción con los siguientes filtros?\n\n"
        msg += f"Tipos: {', '.join(folder_types) if folder_types else 'Todos'}\n"
        msg += f"Patrón: {config.get('folder_pattern', 'Ninguno')}\n"
        msg += f"Fechas: {config.get('date_from', 'N/A')} - {config.get('date_to', 'N/A')}\n\n"
        msg += "Esto puede tomar varios minutos dependiendo de la cantidad de archivos."
        
        if not messagebox.askyesno("Confirmar Extracción", msg):
            return
        
        # Iniciar en thread
        self.is_extracting = True
        self.results = []
        self._clear_results_table()
        
        thread = Thread(target=self._extraction_thread, args=(config,), daemon=True)
        thread.start()
    
    def _extraction_thread(self, config):
        """Thread de extracción."""
        try:
            self._log("Iniciando extracción...", "INFO")
            
            def progress_callback(current, total, info):
                status = info.get('status', 'extracting')
                
                if status == 'scanning':
                    self.after(0, lambda: self.progress_label.config(
                        text=f"Escaneando archivos... Procesados: {current}"
                    ))
                else:
                    file_name = info.get('file', '')
                    urls_count = info.get('urls_extracted', 0)
                    errors = info.get('errors', 0)
                    
                    if total:
                        percentage = (current / total) * 100
                        self.after(0, lambda p=percentage: self.progress_bar.config(value=p))
                        
                        self.after(0, lambda: self.progress_label.config(
                            text=f"Procesando: {current}/{total} archivos"
                        ))
                        
                        self.after(0, lambda: self.stats_label.config(
                            text=f"URLs: {urls_count} | Errores: {errors}"
                        ))
                    
                    if file_name:
                        self.after(0, lambda fn=file_name: self._log(f"Procesando: {fn}", "INFO"))
            
            # Ejecutar extracción
            results = self.extractor.extract_urls(
                config,
                progress_callback=progress_callback,
                url_cache=self.url_cache
            )
            
            self.results = results
            
            # Actualizar UI
            self.after(0, lambda: self._populate_results_table(results))
            self.after(0, lambda: self._log(f"✅ Extracción completada: {len(results)} URLs", "SUCCESS"))
            
            # Estadísticas
            stats = self.extractor.get_extraction_stats()
            stats_msg = f"Total: {stats['total_found']} | Extraídas: {stats['urls_extracted']} | "
            stats_msg += f"Cache: {stats['cached']} | Errores: {stats['errors']}"
            self.after(0, lambda msg=stats_msg: self._log(msg, "INFO"))
            
        except Exception as e:
            self.after(0, lambda: self._log(f"❌ Error: {str(e)}", "ERROR"))
            log.error(f"Error en extracción: {e}")
        finally:
            self.is_extracting = False
            self.after(0, lambda: self.progress_bar.config(value=0))
    
    def _stop_extraction(self):
        """Detiene la extracción."""
        if not self.is_extracting:
            messagebox.showinfo("Info", "No hay extracción en curso")
            return
        
        if self.extractor:
            self.extractor.stop_extraction()
            self._log("Deteniendo extracción...", "WARNING")
    
    def _build_config(self) -> Optional[Dict]:
        """Construye configuración de filtros."""
        config = {
            'root_path': self.root_path.get().strip(),
            'folder_types': [],
            'folder_pattern': self.folder_pattern.get().strip(),
            'rate_limit_pause': float(os.getenv('DROPBOX_RATE_LIMIT_PAUSE', '0.5'))
        }
        
        # Tipos de carpeta
        if self.folder_inicial.get():
            config['folder_types'].append('INICIAL')
        if self.folder_posterior.get():
            config['folder_types'].append('POSTERIOR')
        
        # Fechas
        date_from_str = self.date_from.get().strip()
        date_to_str = self.date_to.get().strip()
        
        try:
            if date_from_str:
                config['date_from'] = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            if date_to_str:
                config['date_to'] = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Usa YYYY-MM-DD")
            return None
        
        return config
    
    # ===================================
    # Métodos de resultados
    # ===================================
    
    def _populate_results_table(self, results: List[Dict]):
        """Llena la tabla con resultados."""
        self._clear_results_table()
        
        for idx, item in enumerate(results, 1):
            # Formatear tamaño
            size_str = self._format_file_size(item.get('size', 0))
            
            # Formatear fecha
            mod_date = item.get('modified', '')
            if mod_date:
                try:
                    dt = datetime.fromisoformat(mod_date)
                    mod_date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            self.results_tree.insert(
                '',
                'end',
                text=str(idx),
                values=(
                    item.get('name', ''),
                    Path(item.get('parent_folder', '')).name,
                    item.get('folder_type', ''),
                    size_str,
                    mod_date
                )
            )
        
        self.results_count_label.config(text=f"{len(results)} URLs extraídas")
    
    def _clear_results_table(self):
        """Limpia la tabla de resultados."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.results_count_label.config(text="0 URLs extraídas")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formatea tamaño de archivo."""
        if not size_bytes:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        unit_idx = 0
        
        while size >= 1024 and unit_idx < len(units) - 1:
            size /= 1024
            unit_idx += 1
        
        return f"{size:.2f} {units[unit_idx]}"
    
    # ===================================
    # Métodos de exportación
    # ===================================
    
    def _export_results(self):
        """Exporta resultados a Excel."""
        if not self.results:
            messagebox.showwarning("Advertencia", "No hay resultados para exportar")
            return
        
        # Seleccionar archivo de salida
        default_name = f"dropbox_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = filedialog.asksaveasfilename(
            title="Guardar Exportación",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("Todos", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            template = self.template_var.get()
            
            if filepath.endswith('.xlsx'):
                success = self.export_service.export_to_excel(self.results, filepath, template)
            elif filepath.endswith('.csv'):
                success = self.export_service.export_to_csv(self.results, filepath, template)
            else:
                messagebox.showerror("Error", "Formato de archivo no soportado")
                return
            
            if success:
                self._log(f"✅ Exportación exitosa: {filepath}", "SUCCESS")
                
                # Preguntar si abrir carpeta
                if messagebox.askyesno("Exportación Exitosa", "¿Abrir carpeta del archivo?"):
                    os.startfile(Path(filepath).parent)
            else:
                self._log("❌ Error al exportar", "ERROR")
                
        except Exception as e:
            self._log(f"❌ Error al exportar: {str(e)}", "ERROR")
            log.error(f"Error en exportación: {e}")
    
    def _save_to_db(self):
        """Guarda resultados en base de datos."""
        if not self.results:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar")
            return
        
        try:
            saved_count = 0
            updated_count = 0
            
            for item in self.results:
                existing = self.db.get_dropbox_url_by_path(item['path'])
                
                self.db.save_dropbox_url(
                    file_path=item['path'],
                    file_name=item['name'],
                    folder_type=item.get('folder_type', 'DESCONOCIDO'),
                    shared_url=item['url'],
                    file_size=item.get('size'),
                    modified_date=item.get('modified')
                )
                
                if existing:
                    updated_count += 1
                else:
                    saved_count += 1
            
            msg = f"✅ Guardado en BD: {saved_count} nuevas, {updated_count} actualizadas"
            self._log(msg, "SUCCESS")
            messagebox.showinfo("Éxito", msg)
            
            # Actualizar cache
            self._load_url_cache()
            
        except Exception as e:
            self._log(f"❌ Error al guardar en BD: {str(e)}", "ERROR")
            log.error(f"Error al guardar en DB: {e}")
    
    # ===================================
    # Métodos de menú contextual
    # ===================================
    
    def _show_context_menu(self, event):
        """Muestra menú contextual."""
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _copy_url(self):
        """Copia URL al portapapeles."""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        idx = int(self.results_tree.item(selection[0])['text']) - 1
        if 0 <= idx < len(self.results):
            url = self.results[idx].get('url', '')
            self.clipboard_clear()
            self.clipboard_append(url)
            self._log(f"URL copiada al portapapeles", "INFO")
    
    def _open_url(self):
        """Abre URL en navegador."""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        idx = int(self.results_tree.item(selection[0])['text']) - 1
        if 0 <= idx < len(self.results):
            url = self.results[idx].get('url', '')
            import webbrowser
            webbrowser.open(url)
    
    # ===================================
    # Métodos de utilidad
    # ===================================
    
    def _log(self, message: str, level: str = "INFO"):
        """Agrega mensaje al log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Colores por nivel
        colors = {
            'INFO': '#00d4ff',
            'SUCCESS': '#00ff88',
            'WARNING': '#ffbb00',
            'ERROR': '#ff4444'
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.log_text.insert(tk.END, f"{message}\n", level.lower())
        
        # Configurar tags de color
        self.log_text.tag_config('timestamp', foreground='#888888')
        for lvl, color in colors.items():
            self.log_text.tag_config(lvl.lower(), foreground=color)
        
        # Auto-scroll
        self.log_text.see(tk.END)
    
    def refresh(self):
        """Refresca el tab."""
        pass
