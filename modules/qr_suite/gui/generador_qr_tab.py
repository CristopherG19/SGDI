"""
SGDI - Tab Generador de QR
===========================

Interfaz gráfica para generación simple e interactiva de códigos QR.

Este módulo proporciona un tab GUI para la ventana principal que permite
generar códigos QR de forma individual o en lote, con configuración
personalizable de tamaño, corrección de errores, y vista previa en tiempo real.

Features:
    - Generación individual o por lotes (separados por '|')
    - Vista previa en tiempo real del QR generado
    - Configuración de tamaño (100-1000 px)
    - Niveles de corrección de errores ajustables
    - Exportación con nombres personalizados
    - Barra de progreso para generación por lotes

UI Components:
    - Panel de configuración (izquierda): entrada de texto, opciones
    - Panel de vista previa (derecha): visualización del QR generado

Author:
    SGDI Development Team

Version:
    1.0.0
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk
from typing import List

from modules.qr_suite.services.qr_generator import QRGenerator
from core.utils.logger import get_logger
from config.settings import Settings

log = get_logger(__name__)


class GeneradorQRTab(ttk.Frame):
    """Tab GUI para generación interactiva de códigos QR.
    
    Proporciona una interfaz completa para generar códigos QR con vista previa
    en tiempo real. Soporta generación individual y por lotes con configuración
    avanzada de tamaño y corrección de errores.
    
    Attributes:
        generator (QRGenerator): Instancia del servicio generador de QR
        current_preview_path (str): Ruta del último QR generado para preview
        texto_qr (tk.StringVar): Variable para el contenido del QR
        carpeta_salida (tk.StringVar): Variable para carpeta de exportación
        tamano (tk.IntVar): Variable para tamaño del QR (100-1000 px)
        error_correction (tk.StringVar): Nivel de corrección ('L','M','Q','H')
        error_correction_display (tk.StringVar): Texto visible del nivel
    
    Example:
        >>> from tkinter import Tk
        >>> root = Tk()
        >>> tab = GeneradorQRTab(root)
        >>> tab.pack()
    
    Note:
        Este tab se integra con MainWindow a través del sidebar.
        Los QRs generados se guardan por defecto en Settings.EXPORTS_DIR.
    """
    
    def __init__(self, parent):
        """Inicializa el tab generador de QR con todos sus componentes.
        
        Configura las variables de control, instancia el servicio generador,
        y construye la interfaz gráfica completa con paneles de configuración
        y vista previa.
        
        Args:
            parent (tk.Widget): Widget padre (generalmente un Notebook o Frame).
        """
        super().__init__(parent, padding=20)
        
        self.generator = QRGenerator()
        self.current_preview_path = None
        
        # Variables
        self.texto_qr = tk.StringVar()
        self.carpeta_salida = tk.StringVar(value=str(Settings.EXPORTS_DIR))
        self.tamano = tk.IntVar(value=Settings.QR_DEFAULT_SIZE)
        self.error_correction = tk.StringVar(value="M")
        self.error_correction_display = tk.StringVar(value="Media (15%)")
        
        # Crear interfaz
        self._create_ui()
        
        log.debug("Generador QR tab inicializado")
    
    def _create_ui(self):
        """Crea la interfaz del generador de QR."""
        # Configurar grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        
        # Panel izquierdo: Configuración
        self._create_config_panel()
        
        # Panel derecho: Vista previa
        self._create_preview_panel()
    
    def _create_config_panel(self):
        """Crea el panel de configuración."""
        config_frame = ttk.Frame(self)
        config_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Título
        ttk.Label(
            config_frame,
            text="🔲 Generador Simple de QR",
            font=("Segoe UI", 20, "bold"),
            bootstyle="primary"
        ).pack(anchor=W, pady=(0, 20))
        
        # Entrada de texto
        input_frame = ttk.LabelFrame(
            config_frame,
            text="Contenido del QR",
            padding=15
        )
        input_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            input_frame,
            text="Texto o URL:",
            font=("Segoe UI", 10)
        ).pack(anchor=W, pady=(0, 5))
        
        text_entry = ttk.Text(
            input_frame,
            height=4,
            wrap=WORD,
            font=("Segoe UI", 10)
        )
        text_entry.pack(fill=X, pady=(0, 5))
        
        # Sincronizar con StringVar
        def on_text_change(*args):
            self.texto_qr.set(text_entry.get("1.0", "end-1c"))
        
        text_entry.bind('<KeyRelease>', on_text_change)
        
        ttk.Label(
            input_frame,
            text="💡 Tip: Para múltiples QRs, separe con '|' (ej: 123|456|789)",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W)
        
        # Configuración avanzada
        advanced_frame = ttk.LabelFrame(
            config_frame,
            text="Configuración",
            padding=15
        )
        advanced_frame.pack(fill=X, pady=(0, 15))
        
        # Grid para config
        advanced_frame.columnconfigure(1, weight=1)
        
        # Carpeta de salida
        ttk.Label(
            advanced_frame,
            text="Carpeta:",
            font=("Segoe UI", 10)
        ).grid(row=0, column=0, sticky=W, pady=5)
        
        folder_frame = ttk.Frame(advanced_frame)
        folder_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        folder_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(
            folder_frame,
            textvariable=self.carpeta_salida,
            font=("Segoe UI", 9)
        ).pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        
        ttk.Button(
            folder_frame,
            text="📁",
            command=self._select_folder,
            width=3,
            bootstyle="secondary-outline"
        ).pack(side=RIGHT)
        
        # Tamaño
        ttk.Label(
            advanced_frame,
            text="Tamaño:",
            font=("Segoe UI", 10)
        ).grid(row=1, column=0, sticky=W, pady=5)
        
        ttk.Spinbox(
            advanced_frame,
            from_=100,
            to=1000,
            textvariable=self.tamano,
            width=10,
            font=("Segoe UI", 10)
        ).grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        ttk.Label(
            advanced_frame,
            text="píxeles",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).grid(row=1, column=2, sticky=W, pady=5)
        
        # Corrección de errores
        ttk.Label(
            advanced_frame,
            text="Corrección:",
            font=("Segoe UI", 10)
        ).grid(row=2, column=0, sticky=W, pady=5)
        
        error_options = [
            ("Baja (7%)", "L"),
            ("Media (15%)", "M"),
            ("Alta (25%)", "Q"),
            ("Muy Alta (30%)", "H")
        ]
        
        error_combo = ttk.Combobox(
            advanced_frame,
            textvariable=self.error_correction_display,
            values=[opt[0] for opt in error_options],
            state="readonly",
            width=15,
            font=("Segoe UI", 10)
        )
        error_combo.grid(row=2, column=1, columnspan=2, sticky=W, padx=5, pady=5)
        error_combo.current(1)  # Media por defecto
        
        # Mapeo de valores
        def on_error_change(*args):
            selected = self.error_correction_display.get()
            for label, value in error_options:
                if label == selected:
                    self.error_correction.set(value)
                    break
        
        self.error_correction_display.trace_add('write', on_error_change)
        
        # Botones de acción
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="✨ Generar QR",
            command=self._generate_qr,
            bootstyle="primary",
            width=20
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="💾 Guardar Como...",
            command=self._save_as,
            bootstyle="success-outline",
            width=20
        ).pack(side=LEFT)
    
    def _create_preview_panel(self):
        """Crea el panel de vista previa."""
        preview_frame = ttk.LabelFrame(
            self,
            text="Vista Previa",
            padding=20
        )
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.rowconfigure(0, weight=1)
        
        # Canvas para la imagen
        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg="#2b3e50",
            highlightthickness=0,
            width=400,
            height=400
        )
        self.preview_canvas.pack(expand=YES, fill=BOTH)
        
        # Mensaje inicial
        self.preview_canvas.create_text(
            200, 200,
            text="Genera un QR para ver\nla vista previa aquí",
            font=("Segoe UI", 14),
            fill="#adb5bd",
            tags="placeholder",
            justify=CENTER
        )
        
        # Info del QR generado
        self.info_label = ttk.Label(
            preview_frame,
            text="",
            font=("Segoe UI", 9),
            bootstyle="secondary",
            justify=CENTER
        )
        self.info_label.pack(pady=(10, 0))
    
    def _select_folder(self):
        """Abre diálogo para seleccionar carpeta."""
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta de salida",
            initialdir=self.carpeta_salida.get()
        )
        if folder:
            self.carpeta_salida.set(folder)
    
    def _generate_qr(self):
        """Genera el código QR."""
        texto = self.texto_qr.get().strip()
        
        if not texto:
            messagebox.showwarning(
                "Advertencia",
                "Por favor ingrese el contenido del QR"
            )
            return
        
        try:
            # Verificar si hay múltiples
            textos = [t.strip() for t in texto.split('|') if t.strip()]
            
            if len(textos) > 1:
                self._generate_batch(textos)
            else:
                self._generate_single(textos[0])
                
        except Exception as e:
            log.error(f"Error al generar QR: {e}")
            messagebox.showerror(
                "Error",
                f"Error al generar QR:\n{str(e)}"
            )
    
    def _generate_single(self, content: str):
        """Genera un solo QR."""
        output_folder = Path(self.carpeta_salida.get())
        output_path = output_folder / "qr_generado.png"
        
        # Generar
        success, result = self.generator.generate_single(
            content=content,
            output_path=output_path,
            size=self.tamano.get(),
            error_correction=self.error_correction.get()
        )
        
        if success:
            self.current_preview_path = result
            self._show_preview(result)
            self.info_label.config(
                text=f"✅ QR generado: {Path(result).name}\n"
                     f"Tamaño: {self.tamano.get()}x{self.tamano.get()} px"
            )
            
            messagebox.showinfo(
                "Éxito",
                f"Código QR generado exitosamente:\n{result}"
            )
        else:
            messagebox.showerror("Error", result)
    
    def _generate_batch(self, contents: List[str]):
        """Genera múltiples QRs."""
        output_folder = Path(self.carpeta_salida.get())
        
        # Ventana de progreso
        progress_window = tk.Toplevel(self)
        progress_window.title("Generando QRs...")
        progress_window.geometry("400x150")
        progress_window.transient(self)
        progress_window.grab_set()
        
        ttk.Label(
            progress_window,
            text=f"Generando {len(contents)} códigos QR...",
            font=("Segoe UI", 12)
        ).pack(pady=20)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window,
            variable=progress_var,
            maximum=len(contents),
            bootstyle="success",
            length=350
        )
        progress_bar.pack(pady=10)
        
        status_label = ttk.Label(
            progress_window,
            text="Iniciando...",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        )
        status_label.pack()
        
        # Callback de progreso
        def update_progress(current, total):
            progress_var.set(current)
            status_label.config(text=f"{current} de {total} completados")
            progress_window.update()
        
        # Generar en batch
        results = self.generator.generate_batch(
            contents=contents,
            output_folder=output_folder,
            size=self.tamano.get(),
            progress_callback=update_progress
        )
        
        progress_window.destroy()
        
        # Mostrar resultado
        if results:
            first_path = list(results.values())[0]
            self.current_preview_path = first_path
            self._show_preview(first_path)
            self.info_label.config(
                text=f"✅ {len(results)} QRs generados en batch"
            )
            
            messagebox.showinfo(
                "Éxito",
                f"Se generaron {len(results)} de {len(contents)} códigos QR\n"
                f"Carpeta: {output_folder}"
            )
        else:
            messagebox.showerror(
                "Error",
                "No se pudieron generar los códigos QR"
            )
    
    def _show_preview(self, image_path: str):
        """
        Muestra la vista previa del QR.
        
        Args:
            image_path: Ruta de la imagen QR
        """
        try:
            # Limpiar canvas
            self.preview_canvas.delete("all")
            
            # Cargar imagen
            img = Image.open(image_path)
            
            # Redimensionar para ajustar al canvas
            canvas_size = min(self.preview_canvas.winfo_width(), 
                            self.preview_canvas.winfo_height())
            if canvas_size <= 1:
                canvas_size = 400
            
            img.thumbnail((canvas_size - 40, canvas_size - 40), Image.Resampling.LANCZOS)
            
            # Convertir para tkinter
            photo = ImageTk.PhotoImage(img)
            
            # Mostrar en canvas (centrado)
            x = self.preview_canvas.winfo_width() // 2
            y = self.preview_canvas.winfo_height() // 2
            if x <= 1:
                x, y = 200, 200
            
            self.preview_canvas.create_image(
                x, y,
                image=photo,
                tags="qr_image"
            )
            
            # Mantener referencia
            self.preview_canvas.image = photo
            
            log.debug(f"Vista previa mostrada: {image_path}")
            
        except Exception as e:
            log.error(f"Error al mostrar vista previa: {e}")
            self.preview_canvas.create_text(
                200, 200,
                text=f"Error al cargar vista previa:\n{str(e)}",
                font=("Segoe UI", 10),
                fill="#e74c3c",
                justify=CENTER
            )
    
    def _save_as(self):
        """Guarda el QR actual con un nombre personalizado."""
        if not self.current_preview_path:
            messagebox.showwarning(
                "Advertencia",
                "Primero genera un código QR"
            )
            return
        
        # Diálogo para guardar
        filename = filedialog.asksaveasfilename(
            title="Guardar QR como...",
            defaultextension=".png",
            filetypes=[
                ("Imagen PNG", "*.png"),
                ("Imagen JPEG", "*.jpg"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if filename:
            try:
                img = Image.open(self.current_preview_path)
                img.save(filename)
                messagebox.showinfo(
                    "Éxito",
                    f"QR guardado como:\n{filename}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al guardar:\n{str(e)}"
                )
    
    def refresh(self):
        """Refresca el tab (llamado desde MainWindow)."""
        log.debug("Generador QR tab refrescado")
        # No hay datos que refrescar en este tab

