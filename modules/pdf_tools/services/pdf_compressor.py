"""
SGDI - Servicio Compresor de PDFs
==================================

Compresión de archivos PDF mediante optimización de imágenes.
"""

import os
import io
import time
from pathlib import Path
from typing import Optional, Callable, Dict, List, Tuple

from PIL import Image
import PyPDF2
from PyPDF2.generic import ByteStringObject

from core.utils.logger import get_logger, log_operation
from core.database.simple_db import get_db

log = get_logger(__name__)


class PDFCompressor:
    """Compresor de archivos PDF."""
    
    def __init__(self):
        """Inicializa el compresor."""
        self.db = get_db()
        self.stop_requested = False
    
    def stop(self):
        """Detiene la compresión."""
        self.stop_requested = True
        log.info("Deteniendo compresión de PDFs...")
    
    def analyze_folder(self, 
                      folder_path: str | Path,
                      progress_callback: Optional[Callable] = None) -> Dict:
        """
        Analiza carpeta buscando PDFs.
        
        Args:
            folder_path: Carpeta a analizar
            progress_callback: Callback de progreso
            
        Returns:
            Diccionario con estadísticas
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            log.error(f"Carpeta no existe: {folder_path}")
            return {"pdf_files": [], "total_size": 0, "folder_count": 0}
        
        pdf_files = []
        total_size = 0
        folder_count = 0
        
        log.info(f"Analizando carpeta: {folder_path}")
        
        try:
            for root, _, files in os.walk(folder_path):
                if self.stop_requested:
                    break
                
                folder_count += 1
                
                for file in files:
                    if file.lower().endswith('.pdf'):
                        file_path = Path(root) / file
                        pdf_files.append(str(file_path))
                        total_size += file_path.stat().st_size
                
                if progress_callback and folder_count % 10 == 0:
                    progress_callback(folder_count, len(pdf_files))
        
        except Exception as e:
            log.error(f"Error analizando carpeta: {e}")
        
        log.info(f"Análisis completado: {len(pdf_files)} PDFs, {total_size / (1024*1024):.2f} MB")
        
        return {
            "pdf_files": pdf_files,
            "total_size": total_size,
            "folder_count": folder_count
        }
    
    def compress_pdf(self,
                    input_path: str | Path,
                    quality: int = 70) -> Tuple[int, int]:
        """
        Comprime un PDF individual.
        
        Args:
            input_path: Ruta del PDF
            quality: Calidad JPEG (1-100)
            
        Returns:
            Tupla (tamaño_original, tamaño_nuevo)
        """
        input_path = Path(input_path)
        output_path = input_path.with_suffix('.pdf.tmp')
        
        original_size = input_path.stat().st_size
        
        try:
            with open(input_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    # Optimizar imágenes en la página
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        
                        for obj in xObject:
                            if xObject[obj]['/Subtype'] == '/Image':
                                original = xObject[obj]
                                
                                try:
                                    data = original.get_data()
                                    img = Image.open(io.BytesIO(data))
                                    
                                    # Convertir a RGB si es necesario
                                    if img.mode in ('RGBA', 'LA'):
                                        img = img.convert('RGB')
                                    
                                    # Comprimir imagen
                                    buf = io.BytesIO()
                                    img.save(buf, format='JPEG', quality=quality, optimize=True)
                                    original.set_data(ByteStringObject(buf.getvalue()))
                                    
                                except Exception as e:
                                    log.debug(f"Error optimizando imagen: {e}")
                    
                    writer.add_page(page)
                
                # Guardar temporal
                with open(output_path, 'wb') as out:
                    writer.write(out)
            
            new_size = output_path.stat().st_size
            
            # Reemplazar solo si es más pequeño
            if new_size < original_size:
                output_path.replace(input_path)
                log.debug(f"PDF comprimido: {input_path.name} ({original_size - new_size} bytes ahorrados)")
            else:
                output_path.unlink()
                new_size = original_size
                log.debug(f"PDF sin reducción: {input_path.name}")
            
            return original_size, new_size
            
        except Exception as e:
            log.error(f"Error comprimiendo {input_path}: {e}")
            if output_path.exists():
                output_path.unlink()
            return original_size, original_size
    
    def compress_folder(self,
                       folder_path: str | Path,
                       quality: int = 70,
                       progress_callback: Optional[Callable] = None) -> Dict:
        """
        Comprime todos los PDFs en una carpeta.
        
        Args:
            folder_path: Carpeta con PDFs
            quality: Calidad JPEG
            progress_callback: Callback(idx, total, nombre_archivo, estado)
            
        Returns:
            Estadísticas de compresión
        """
        self.stop_requested = False
        start_time = time.time()
        
        # Analizar carpeta
        analysis = self.analyze_folder(folder_path)
        pdf_files = analysis['pdf_files']
        
        if not pdf_files:
            log.warning("No se encontraron archivos PDF")
            return {
                "total": 0,
                "compressed": 0,
                "skipped": 0,
                "errors": 0,
                "saved_bytes": 0,
                "original_bytes": 0,
                "duration": 0
            }
        
        stats = {
            "total": len(pdf_files),
            "compressed": 0,
            "skipped": 0,
            "errors": 0,
            "saved_bytes": 0,
            "original_bytes": 0
        }
        
        log.info(f"Iniciando compresión de {len(pdf_files)} PDFs...")
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            if self.stop_requested:
                log.warning("Compresión detenida por usuario")
                break
            
            try:
                if progress_callback:
                    progress_callback(idx, len(pdf_files), Path(pdf_path).name, "Procesando")
                
                orig_size, new_size = self.compress_pdf(pdf_path, quality)
                
                stats["original_bytes"] += orig_size
                
                if new_size < orig_size:
                    saved = orig_size - new_size
                    stats["saved_bytes"] += saved
                    stats["compressed"] += 1
                    
                    if progress_callback:
                        progress_callback(idx, len(pdf_files), Path(pdf_path).name, f"✓ Ahorrado {saved/1024:.1f} KB")
                else:
                    stats["skipped"] += 1
                    
                    if progress_callback:
                        progress_callback(idx, len(pdf_files), Path(pdf_path).name, "➡ Sin reducción")
                        
            except Exception as e:
                stats["errors"] += 1
                log.error(f"Error procesando {pdf_path}: {e}")
                
                if progress_callback:
                    progress_callback(idx, len(pdf_files), Path(pdf_path).name, f"✗ Error")
        
        duration = time.time() - start_time
        stats["duration"] = duration
        
        # Registrar operación
        log_operation(
            module="pdf_compressor",
            action="compress_folder",
            success=stats["errors"] == 0,
            message=f"Comprimidos {stats['compressed']} de {stats['total']} PDFs",
            total=stats["total"],
            compressed=stats["compressed"],
            saved_mb=stats["saved_bytes"] / (1024*1024),
            duration=duration
        )
        
        # Guardar en BD
        try:
            self.db.save_pdf_compression(
                folder_path=str(folder_path),
                files_total=stats["total"],
                files_compressed=stats["compressed"],
                files_skipped=stats["skipped"],
                files_error=stats["errors"],
                bytes_saved=stats["saved_bytes"],
                bytes_original=stats["original_bytes"],
                duration=duration
            )
        except Exception as e:
            log.warning(f"No se pudo guardar en BD: {e}")
        
        log.info(f"Compresión completada en {duration:.1f}s: {stats['saved_bytes']/(1024*1024):.2f} MB ahorrados")
        
        return stats
