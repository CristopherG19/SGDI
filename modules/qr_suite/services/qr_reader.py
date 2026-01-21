"""
SGDI - Servicio Lector de QR
=============================

Servicio para lectura de códigos QR desde archivos PDF e imágenes.
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
    """Lector de códigos QR desde archivos."""
    
    def __init__(self):
        """Inicializa el lector de QR."""
        self.db = get_db()
        self.stop_requested = False
    
    def read_from_image(self, image_path: str | Path) -> Tuple[bool, Optional[str], str]:
        """
        Lee código QR desde una imagen.
        
        Args:
            image_path: Ruta de la imagen
            
        Returns:
            Tupla (éxito, contenido_qr, mensaje)
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
        """
        Lee código QR desde un PDF (primera página).
        
        Args:
            pdf_path: Ruta del PDF
            poppler_path: Ruta a poppler (opcional)
            
        Returns:
            Tupla (éxito, contenido_qr, mensaje)
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
        """
        Procesa un archivo: lee QR y lo mueve/renombra.
        
        Args:
            file_path: Ruta del archivo original
            output_folder: Carpeta para archivos procesados
            error_folder: Carpeta para archivos sin QR
            poppler_path: Ruta a poppler (para PDFs)
            duplicate_policy: "renombrar", "sobrescribir", "saltar"
            
        Returns:
            Diccionario con resultado del procesamiento
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
        """
        Maneja archivos duplicados según la política.
        
        Args:
            dest_path: Ruta destino
            source_path: Ruta origen
            policy: "renombrar", "sobrescribir", "saltar", "comparar"
            
        Returns:
            Path modificado o None si se salta
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
        """Genera ruta única agregando sufijo numérico."""
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
        """Calcula MD5 de un archivo."""
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
        """
        Procesa todos los archivos de un directorio.
        
        Args:
            input_folder: Carpeta de entrada
            output_folder: Carpeta de salida
            error_folder: Carpeta de error
            poppler_path: Ruta a poppler
            duplicate_policy: Política de duplicados
            progress_callback: Callback(idx, total, filename, result)
            
        Returns:
            Estadísticas del procesamiento
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
        """Detiene el procesamiento."""
        self.stop_requested = True
        log.info("Deteniendo procesamiento de QR...")
