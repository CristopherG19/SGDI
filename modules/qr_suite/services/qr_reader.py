"""
SGDI - Servicio Lector de QR
=============================

Servicio para lectura de códigos QR desde archivos PDF e imágenes.

Este módulo proporciona funcionalidades completas para leer códigos QR desde
archivos PDF e imágenes, renombrar archivos automáticamente basándose en el
contenido del QR, y procesar directorios completos de forma batch. Incluye
manejo inteligente de duplicados, validación de archivos, y registro de
operaciones para auditoría.

Supported Formats:
    - PDFs: Requiere poppler-utils instalado
    - Imágenes: PNG, JPG, JPEG, TIFF, BMP

Examples:
    Lectura simple de un QR desde imagen::

        reader = QRReader()
        success, content, msg = reader.read_from_image("documento.png")
        if success:
            print(f"QR encontrado: {content}")

    Procesar directorio completo::

        stats = reader.process_directory(
            input_folder="./scans/",
            output_folder="./procesados/",
            error_folder="./sin_qr/",
            duplicate_policy="renombrar"
        )
        print(f"Procesados: {stats['exitosos']} archivos")

Author:
    SGDI Development Team

Version:
    1.0.0
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
from pyzbar.pyzbar import decode
from PIL import Image
from pdf2image import convert_from_path
import hashlib
import shutil

from core.utils.logger import get_logger, log_operation
from core.utils.file_handler import ensure_directory, sanitize_filename
from core.utils.validators import validate_pdf_file, validate_image_file
from core.database.simple_db import get_db
from config.settings import Settings

log = get_logger(__name__)


class QRReader:
    """Lector profesional de códigos QR con soporte para PDFs e imágenes.
    
    Esta clase proporciona métodos para leer códigos QR desde archivos PDF
    e imágenes, con capacidades de procesamiento por lotes, renombrado
    automático basado en contenido QR, y manejo inteligente de duplicados.
    Todas las operaciones se registran en la base de datos para auditoría.
    
    Attributes:
        db: Instancia de la base de datos para registro de operaciones
        stop_requested (bool): Bandera para detener procesamiento batch
    
    Example:
        >>> reader = QRReader()
        >>> success, content, msg = reader.read_from_image("qr_code.png")
        >>> if success:
        ...     print(f"QR: {content}")
    """
    
    def __init__(self):
        """Inicializa el lector de QR.
        
        Configura la conexión a la base de datos y la bandera de control
        para procesamiento por lotes.
        """
        self.db = get_db()
        self.stop_requested = False
    
    def read_from_image(self, image_path: str | Path) -> Tuple[bool, Optional[str], str]:
        """Lee y decodifica un código QR desde un archivo de imagen.
        
        Abre una imagen, la decodifica buscando códigos QR y retorna el
        contenido del primer código QR encontrado. La imagen se valida
        antes de procesarla.
        
        Args:
            image_path (str | Path): Ruta absoluta o relativa al archivo de imagen.
                Formatos soportados: PNG, JPG, JPEG, TIFF, BMP.
            
        Returns:
            Tuple[bool, Optional[str], str]: Una tupla de 3 elementos:
                - bool: True si se leyó el QR exitosamente, False en caso contrario
                - Optional[str]: Contenido del QR si fue exitoso, None si falló
                - str: Mensaje descriptivo del resultado o error
        
        Example:
            >>> reader = QRReader()
            >>> success, content, msg = reader.read_from_image("badge.png")
            >>> if success:
            ...     print(f"Contenido QR: {content}")
            ... else:
            ...     print(f"Error: {msg}")
        
        Note:
            - Solo se retorna el primer QR encontrado si hay múltiples
            - La imagen debe ser legible y contener un QR válido
            - Se registra en logs el contenido (primeros 50 caracteres)
        """
        try:
            # Validar imagen
            valid, msg = validate_image_file(image_path)
            if not valid:
                return False, None, msg
            
            # Abrir imagen
            img = Image.open(image_path)
            
            # Decodificar QR
            decoded_objects = decode(img)
            
            if not decoded_objects:
                return False, None, "No se encontró código QR en la imagen"
            
            # Obtener primer QR
            qr_data = decoded_objects[0].data.decode('utf-8')
            
            log.debug(f"QR leído: {qr_data[:50]}...")
            return True, qr_data, "QR leído exitosamente"
            
        except Exception as e:
            error_msg = f"Error al leer QR: {e}"
            log.error(error_msg)
            return False, None, error_msg
    
    def read_from_pdf(self, 
                     pdf_path: str | Path,
                     poppler_path: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
        """Lee y decodifica un código QR desde la primera página de un PDF.
        
        Convierte la primera página del PDF a imagen usando pdf2image y poppler,
        luego busca y decodifica el código QR. Requiere poppler-utils instalado.
        
        Args:
            pdf_path (str | Path): Ruta al archivo PDF a procesar.
            poppler_path (str, optional): Ruta al directorio de binarios de poppler.
                Si no se especifica, se busca en las rutas del sistema.
                Necesario en Windows. Defaults to None.
            
        Returns:
            Tuple[bool, Optional[str], str]: Una tupla de 3 elementos:
                - bool: True si se leyó el QR exitosamente, False en caso contrario
                - Optional[str]: Contenido del QR si fue exitoso, None si falló
                - str: Mensaje descriptivo del resultado o error
        
        Example:
            >>> reader = QRReader()
            >>> success, content, msg = reader.read_from_pdf(
            ...     "factura.pdf",
            ...     poppler_path="C:/poppler/bin"
            ... )
            >>> if success:
            ...     print(f"Factura #{content}")
        
        Note:
            - Solo procesa la primera página del PDF
            - DPI de conversión: 150 (balance entre calidad y velocidad)
            - Requiere poppler-utils: en Windows descargar binarios,
              en Linux: apt-get install poppler-utils
        """
        try:
            # Validar PDF
            valid, msg = validate_pdf_file(pdf_path)
            if not valid:
                return False, None, msg
            
            # Convertir primera página a imagen
            if poppler_path and os.path.exists(poppler_path):
                images = convert_from_path(
                    pdf_path,
                    first_page=1,
                    last_page=1,
                    dpi=150,
                    poppler_path=poppler_path
                )
            else:
                images = convert_from_path(
                    pdf_path,
                    first_page=1,
                    last_page=1,
                    dpi=150
                )
            
            if not images:
                return False, None, "No se pudo convertir PDF a imagen"
            
            # Decodificar QR de la imagen
            first_page = images[0]
            decoded_objects = decode(first_page)
            
            if not decoded_objects:
                return False, None, "No se encontró código QR en el PDF"
            
            # Obtener primer QR
            qr_data = decoded_objects[0].data.decode('utf-8')
            
            log.debug(f"QR leído desde PDF: {qr_data[:50]}...")
            return True, qr_data, "QR leído exitosamente"
            
        except Exception as e:
            error_msg = f"Error al leer PDF: {e}"
            log.error(error_msg)
            return False, None, error_msg
    
    def process_file(self,
                    file_path: str | Path,
                    output_folder: str | Path,
                    error_folder: str | Path,
                    poppler_path: Optional[str] = None,
                    duplicate_policy: str = "renombrar") -> Dict[str, any]:
        """Procesa un archivo individual: lee su QR y lo renombra/mueve.
        
        Lee el código QR del archivo, lo renombra usando el contenido del QR
        como nombre, y lo mueve a la carpeta de salida. Si no tiene QR, se
        mueve a la carpeta de errores. Maneja duplicados según la política.
        
        Args:
            file_path (str | Path): Ruta del archivo a procesar.
            output_folder (str | Path): Carpeta destino para archivos procesados
                exitosamente (con QR). Se crea si no existe.
            error_folder (str | Path): Carpeta destino para archivos sin QR
                o con errores. Se crea si no existe.
            poppler_path (str, optional): Ruta a poppler (solo para PDFs).
                Defaults to None.
            duplicate_policy (str, optional): Política para manejar duplicados:
                - "renombrar": Agrega sufijo numérico (_1, _2, etc.)
                - "sobrescribir": Reemplaza el archivo existente
                - "saltar": No procesa el archivo duplicado
                - "comparar": Compara MD5, solo renombra si son diferentes
                Defaults to "renombrar".
            
        Returns:
            Dict[str, any]: Diccionario con resultado del procesamiento:
                - success (bool): True si el archivo fue procesado y renombrado
                - qr_content (str): Contenido del QR si fue exitoso
                - final_path (str): Ruta final del archivo
                - action (str): Acción realizada: 'renamed_and_moved',
                  'moved_to_error', 'skipped'
                - message (str): Mensaje descriptivo del resultado
        
        Example:
            >>> reader = QRReader()
            >>> result = reader.process_file(
            ...     file_path="scan001.pdf",
            ...     output_folder="./procesados/",
            ...     error_folder="./errores/",
            ...     duplicate_policy="comparar"
            ... )
            >>> print(f"Resultado: {result['action']} - {result['message']}")
        
        Note:
            - El nombre del archivo se sanitiza (caracteres especiales removidos)
            - La operación exitosa se registra en la base de datos
            - Las carpetas destino se crean automáticamente
        """
        file_path = Path(file_path)
        output_folder = Path(output_folder)
        error_folder = Path(error_folder)
        
        result = {
            'success': False,
            'qr_content': None,
            'final_path': None,
            'action': None,
            'message': ''
        }
        
        try:
            # Leer QR según tipo de archivo
            ext = file_path.suffix.lower()
            
            if ext == '.pdf':
                success, qr_content, msg = self.read_from_pdf(file_path, poppler_path)
            elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                success, qr_content, msg = self.read_from_image(file_path)
            else:
                result['message'] = f"Extensión no soportada: {ext}"
                return result
            
            # Si no hay QR, mover a carpeta de error
            if not success or not qr_content:
                ensure_directory(error_folder)
                dest_path = error_folder / file_path.name
                
                # Manejar duplicados
                dest_path = self._handle_duplicate(dest_path, file_path, "saltar")
                
                shutil.move(str(file_path), str(dest_path))
                
                result['final_path'] = str(dest_path)
                result['action'] = 'moved_to_error'
                result['message'] = msg
                return result
            
            # QR leído exitosamente, renombrar archivo
            sanitized_qr = sanitize_filename(qr_content)
            new_filename = f"{sanitized_qr}{ext}"
            
            ensure_directory(output_folder)
            dest_path = output_folder / new_filename
            
            # Manejar duplicados
            dest_path = self._handle_duplicate(dest_path, file_path, duplicate_policy)
            
            if dest_path:  # Si no se saltó
                shutil.move(str(file_path), str(dest_path))
                
                result['success'] = True
                result['qr_content'] = qr_content
                result['final_path'] = str(dest_path)
                result['action'] = 'renamed_and_moved'
                result['message'] = f"Renombrado a: {dest_path.name}"
                
                # Registrar en BD
                self.db.save_qr_operation(
                    operation_type="read",
                    status="success",
                    file_path=str(dest_path),
                    qr_content=qr_content[:100],
                    items_processed=1,
                    duration=0
                )
            else:
                result['action'] = 'skipped'
                result['message'] = "Archivo saltado (duplicado)"
            
            return result
            
        except Exception as e:
            error_msg = f"Error al procesar {file_path.name}: {e}"
            log.error(error_msg)
            result['message'] = error_msg
            return result
    
    def _handle_duplicate(self,
                         dest_path: Path,
                         source_path: Path,
                         policy: str) -> Optional[Path]:
        """Maneja archivos duplicados según la política especificada.
        
        Método interno para resolver conflictos cuando un archivo con el mismo
        nombre ya existe en la carpeta destino. Aplica la política especificada
        para determinar la acción.
        
        Args:
            dest_path (Path): Ruta destino donde se quiere mover el archivo.
            source_path (Path): Ruta del archivo origen a mover.
            policy (str): Política de manejo de duplicados:
                - "renombrar": Genera nombre único agregando sufijo (_1, _2...)
                - "sobrescribir": Elimina archivo existente y usa el nombre
                - "saltar": No mueve el archivo, retorna None
                - "comparar": Calcula MD5 de ambos archivos:
                  * Si son iguales: salta (retorna None)
                  * Si son diferentes: renombra
            
        Returns:
            Optional[Path]: Path modificado si se debe mover el archivo,
                None si se debe saltar (política "saltar" o archivos idénticos
                en política "comparar").
        
        Note:
            Este método es privado y solo debe ser llamado internamente.
        """
        if not dest_path.exists():
            return dest_path
        
        if policy == "sobrescribir":
            # Eliminar existente
            dest_path.unlink()
            return dest_path
        
        elif policy == "saltar":
            return None
        
        elif policy == "comparar":
            # Comparar por MD5
            source_hash = self._calculate_md5(source_path)
            dest_hash = self._calculate_md5(dest_path)
            
            if source_hash == dest_hash:
                # Son iguales, saltar
                return None
            else:
                # Son diferentes, renombrar
                return self._get_unique_path(dest_path)
        
        else:  # renombrar (default)
            return self._get_unique_path(dest_path)
    
    def _get_unique_path(self, base_path: Path) -> Path:
        """Genera una ruta de archivo única agregando un sufijo numérico.
        
        Si el archivo base ya existe, agrega un sufijo numérico incremental
        (_1, _2, _3...) hasta encontrar un nombre disponible.
        
        Args:
            base_path (Path): Ruta base del archivo.
            
        Returns:
            Path: Ruta única que no existe en el sistema de archivos.
        
        Raises:
            RuntimeError: Si no se puede generar nombre único después
                de 1000 intentos.
        
        Example:
            Si "reporte.pdf" existe, retorna "reporte_1.pdf".
            Si "reporte_1.pdf" también existe, retorna "reporte_2.pdf".
        
        Note:
            Tiene un límite de seguridad de 1000 intentos para evitar
            bucles infinitos.
        """
        if not base_path.exists():
            return base_path
        
        counter = 1
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent
        
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
            
            if counter > 1000:  # Límite de seguridad
                raise RuntimeError("No se pudo generar nombre único")
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calcula el hash MD5 de un archivo.
        
        Lee el archivo en chunks para eficiencia de memoria y calcula
        su hash MD5. Útil para comparar si dos archivos son idénticos.
        
        Args:
            file_path (Path): Ruta al archivo a procesar.
            
        Returns:
            str: Hash MD5 en formato hexadecimal (32 caracteres).
        
        Note:
            Lee en bloques de 4096 bytes para no cargar archivos
            grandes completos en memoria.
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def process_directory(self,
                         input_folder: str | Path,
                         output_folder: str | Path,
                         error_folder: str | Path,
                         poppler_path: Optional[str] = None,
                         duplicate_policy: str = "renombrar",
                         progress_callback: Optional[Callable] = None) -> Dict[str, int]:
        """Procesa todos los archivos con QR de un directorio completo.
        
        Busca todos los archivos soportados en un directorio, lee sus códigos QR,
        los renombra según el contenido del QR y los organiza en carpetas.
        Soporta detención manual durante el proceso.
        
        Args:
            input_folder (str | Path): Carpeta con archivos a procesar.
            output_folder (str | Path): Carpeta destino para archivos procesados
                exitosamente. Se crea si no existe.
            error_folder (str | Path): Carpeta destino para archivos sin QR.
                Se crea si no existe.
            poppler_path (str, optional): Ruta a poppler para procesamiento de PDFs.
                Defaults to None.
            duplicate_policy (str, optional): Política para duplicados:
                "renombrar", "sobrescribir", "saltar", "comparar".
                Defaults to "renombrar".
            progress_callback (Callable, optional): Función de callback llamada
                después de procesar cada archivo. Debe aceptar:
                (idx, total, filename, result_dict). Útil para actualizar
                barras de progreso en GUI. Defaults to None.
            
        Returns:
            Dict[str, int]: Diccionario con estadísticas del procesamiento:
                - procesados (int): Total de archivos procesados
                - exitosos (int): Archivos renombrados exitosamente
                - fallidos (int): Archivos con errores de procesamiento
                - sin_qr (int): Archivos sin código QR
                - duplicados (int): Archivos duplicados encontrados
                - saltados (int): Archivos saltados por política de duplicados
        
        Example:
            >>> reader = QRReader()
            >>> def on_progress(idx, total, filename, result):
            ...     print(f"[{idx}/{total}] {filename}: {result['action']}")
            >>> 
            >>> stats = reader.process_directory(
            ...     input_folder="./scans/",
            ...     output_folder="./organizados/",
            ...     error_folder="./sin_qr/",
            ...     duplicate_policy="comparar",
            ...     progress_callback=on_progress
            ... )
            >>> print(f"Exitosos: {stats['exitosos']}/{stats['procesados']}")
        
        Note:
            - Soporta: PDF, PNG, JPG, JPEG, TIFF, BMP
            - Se puede detener el proceso llamando reader.stop()
            - La operación completa se registra en la base de datos
            - El tiempo total se mide y registra
        """
        import time
        start_time = time.time()
        
        input_folder = Path(input_folder)
        self.stop_requested = False
        
        stats = {
            'procesados': 0,
            'exitosos': 0,
            'fallidos': 0,
            'sin_qr': 0,
            'duplicados': 0,
            'saltados': 0
        }
        
        # Obtener archivos
        extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        files = [
            f for f in input_folder.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ]
        
        if not files:
            log.warning(f"No hay archivos para procesar en {input_folder}")
            return stats
        
        log.info(f"Procesando {len(files)} archivos desde {input_folder}")
        
        # Procesar cada archivo
        for idx, file_path in enumerate(files, 1):
            if self.stop_requested:
                log.warning("Procesamiento detenido por usuario")
                break
            
            result = self.process_file(
                file_path,
                output_folder,
                error_folder,
                poppler_path,
                duplicate_policy
            )
            
            stats['procesados'] += 1
            
            if result['action'] == 'renamed_and_moved':
                stats['exitosos'] += 1
            elif result['action'] == 'moved_to_error':
                stats['sin_qr'] += 1
            elif result['action'] == 'skipped':
                stats['saltados'] += 1
            else:
                stats['fallidos'] += 1
            
            # Callback de progreso
            if progress_callback:
                progress_callback(idx, len(files), file_path.name, result)
        
        duration = time.time() - start_time
        
        # Registrar operación global en BD
        self.db.save_qr_operation(
            operation_type="read_batch",
            status="success",
            items_processed=stats['procesados'],
            duration=duration
        )
        
        log_operation(
            module="qr_reader",
            action="process_directory",
            success=stats['fallidos'] == 0,
            message=f"Procesados {stats['procesados']} archivos en {duration:.2f}s",
            **stats
        )
        
        return stats
    
    def stop(self):
        """Detiene el procesamiento batch en curso.
        
        Marca la bandera stop_requested para que el procesamiento por lotes
        se detenga de manera controlada después de terminar el archivo actual.
        No detiene inmediatamente, sino al inicio de la siguiente iteración.
        
        Example:
            >>> reader = QRReader()
            >>> # En un thread separado:
            >>> reader.process_directory(...)
            >>> # Desde el thread principal:
            >>> reader.stop()  # Detendrá después del archivo actual
        
        Note:
            El procesamiento se detiene de forma segura, completando el
            archivo en proceso antes de terminar.
        """
        self.stop_requested = True
        log.info("Deteniendo procesamiento de QR...")
