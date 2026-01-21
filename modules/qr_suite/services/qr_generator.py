"""
SGDI - Servicio Generador de QR
================================

Servicio para generación de códigos QR individual y en batch.
"""

import qrcode
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

from core.utils.logger import get_logger, log_operation
from core.utils.file_handler import ensure_directory
from core.database.simple_db import get_db
from config.settings import Settings

log = get_logger(__name__)


class QRGenerator:
    """Generador de códigos QR."""
    
    def __init__(self):
        """Inicializa el generador de QR."""
        self.db = get_db()
    
    def generate_single(self, 
                       content: str,
                       output_path: str | Path,
                       size: int = None,
                       error_correction: str = 'L',
                       border: int = 1) -> Tuple[bool, str]:
        """
        Genera un código QR individual.
        
        Args:
            content: Contenido del QR
            output_path: Ruta donde guardar el QR
            size: Tamaño en píxeles (None = auto)
            error_correction: Nivel de corrección ('L', 'M', 'Q', 'H')
            border: Grosor del borde en cajas
            
        Returns:
            Tupla (éxito, mensaje/ruta)
        """
        try:
            if not content.strip():
                return False, "El contenido del QR está vacío"
            
            # Mapear nivel de corrección de errores
            error_levels = {
                'L': qrcode.constants.ERROR_CORRECT_L,  # ~7%
                'M': qrcode.constants.ERROR_CORRECT_M,  # ~15%
                'Q': qrcode.constants.ERROR_CORRECT_Q,  # ~25%
                'H': qrcode.constants.ERROR_CORRECT_H   # ~30%
            }
            error_level = error_levels.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_L)
            
            # Crear QR
            qr = qrcode.QRCode(
                version=1,  # Auto
                error_correction=error_level,
                box_size=10 if size is None else max(1, size // 33),  # Calcular box_size
                border=border,
            )
            
            qr.add_data(content)
            qr.make(fit=True)
            
            # Generar imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionar si se especifica tamaño
            if size:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Asegurar que el directorio existe
            output_path = Path(output_path)
            ensure_directory(output_path.parent)
            
            # Guardar
            img.save(output_path)
            
            log.debug(f"QR generado: {output_path}")
            
            # Registrar en BD
            self.db.save_qr_operation(
                operation_type="generate",
                status="success",
                qr_content=content[:100],  # Primeros 100 caracteres
                file_path=str(output_path),
                items_processed=1,
                duration=0
            )
            
            return True, str(output_path)
            
        except Exception as e:
            error_msg = f"Error al generar QR: {e}"
            log.error(error_msg)
            
            # Registrar error en BD
            self.db.save_qr_operation(
                operation_type="generate",
                status="error",
                qr_content=content[:100] if content else "",
                error_message=str(e),
                items_processed=0,
                duration=0
            )
            
            return False, error_msg
    
    def generate_batch(self,
                      contents: List[str],
                      output_folder: str | Path,
                      size: int = None,
                      prefix: str = "qr_",
                      max_workers: int = 4,
                      progress_callback: Optional[callable] = None) -> Dict[int, str]:
        """
        Genera múltiples códigos QR en paralelo.
        
        Args:
            contents: Lista de contenidos para generar QRs
            output_folder: Carpeta donde guardar los QRs
            size: Tamaño en píxeles
            prefix: Prefijo para nombres de archivo
            max_workers: Número de hilos paralelos
            progress_callback: Callback para reportar progreso (idx, total)
            
        Returns:
            Diccionario {índice: ruta_archivo}
        """
        import time
        start_time = time.time()
        
        output_folder = Path(output_folder)
        ensure_directory(output_folder)
        
        # Filtrar contenidos vacíos
        valid_contents = [
            (i, str(content).strip())
            for i, content in enumerate(contents)
            if str(content).strip()
        ]
        
        log.info(f"Generando {len(valid_contents)} códigos QR en batch")
        
        # Preparar argumentos
        args_list = [
            (idx, content, output_folder / f"{prefix}{idx}.png", size)
            for idx, content in valid_contents
        ]
        
        # Generar en paralelo
        results = {}
        errors = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._generate_worker, args): args[0]
                for args in args_list
            }
            
            for i, future in enumerate(futures):
                idx, path, success = future.result()
                
                if success:
                    results[idx] = path
                else:
                    errors += 1
                
                # Callback de progreso
                if progress_callback:
                    progress_callback(i + 1, len(args_list))
        
        duration = time.time() - start_time
        
        # Registrar operación en BD
        self.db.save_qr_operation(
            operation_type="generate_batch",
            status="success" if errors == 0 else "warning",
            items_processed=len(results),
            duration=duration,
            error_message=f"{errors} errores" if errors > 0 else None
        )
        
        log_operation(
            module="qr_generator",
            action="generate_batch",
            success=errors == 0,
            message=f"Generados {len(results)} de {len(valid_contents)} QRs en {duration:.2f}s",
            total=len(valid_contents),
            success_count=len(results),
            error_count=errors
        )
        
        return results
    
    def _generate_worker(self, args: tuple) -> Tuple[int, str, bool]:
        """
        Worker para generación paralela.
        
        Args:
            args: (índice, contenido, ruta_salida, tamaño)
            
        Returns:
            Tupla (índice, ruta, éxito)
        """
        idx, content, output_path, size = args
        
        try:
            success, result = self.generate_single(content, output_path, size)
            return (idx, result if success else None, success)
        except Exception as e:
            log.error(f"Error en worker QR {idx}: {e}")
            return (idx, None, False)
    
    def generate_with_logo(self,
                          content: str,
                          output_path: str | Path,
                          logo_path: str | Path,
                          size: int = 300) -> Tuple[bool, str]:
        """
        Genera un QR con logo en el centro.
        
        Args:
            content: Contenido del QR
            output_path: Ruta de salida
            logo_path: Ruta del logo
            size: Tamaño final
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            # Generar QR base
            success, qr_path = self.generate_single(content, output_path, size, error_correction='H')
            
            if not success:
                return False, qr_path
            
            # Abrir QR y logo
            qr_img = Image.open(qr_path)
            logo_img = Image.open(logo_path)
            
            # Calcular tamaño del logo (máx 20% del QR)
            logo_size = int(size * 0.2)
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Pegar logo en el centro
            logo_pos = ((size - logo_size) // 2, (size - logo_size) // 2)
            qr_img.paste(logo_img, logo_pos)
            
            # Guardar
            qr_img.save(output_path)
            
            log.info(f"QR con logo generado: {output_path}")
            return True, str(output_path)
            
        except Exception as e:
            error_msg = f"Error al generar QR con logo: {e}"
            log.error(error_msg)
            return False, error_msg
