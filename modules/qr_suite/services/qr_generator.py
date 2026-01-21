"""
SGDI - Servicio Generador de QR
================================

Servicio para generación de códigos QR individual y en batch.

Este módulo proporciona funcionalidades completas para la generación de códigos QR,
incluyendo generación individual, por lotes en paralelo, y códigos QR con logos
personalizados. Todos los códigos QR generados son imágenes PNG con configuración
personalizable de tamaño, corrección de errores y bordes.

Examples:
    Generación simple de un código QR::

        generator = QRGenerator()
        success, path = generator.generate_single(
            content="https://ejemplo.com",
            output_path="./qr_code.png",
            size=300
        )

    Generación por lotes::

        urls = ["url1", "url2", "url3"]
        results = generator.generate_batch(
            contents=urls,
            output_folder="./qr_codes/",
            prefix="qr_"
        )

Author:
    SGDI Development Team

Version:
    1.0.0
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
    """Generador profesional de códigos QR con soporte para batch y personalización.
    
    Esta clase proporciona métodos para generar códigos QR individuales o en lote,
    con opciones avanzadas como niveles de corrección de errores configurables,
    tamaños personalizados, y soporte para agregar logos en el centro del QR.
    Todas las operaciones se registran automáticamente en la base de datos para
    auditoría y seguimiento.
    
    Attributes:
        db: Instancia de la base de datos para registro de operaciones
    
    Example:
        >>> generator = QRGenerator()
        >>> success, path = generator.generate_single(
        ...     content="Hola Mundo",
        ...     output_path="qr.png",
        ...     size=300,
        ...     error_correction='M'
        ... )
        >>> print(f"QR generado: {path}" if success else "Error")
    """
    
    def __init__(self):
        """Inicializa el generador de QR.
        
        Configura la conexión a la base de datos para el registro
        automático de todas las operaciones de generación.
        """
        self.db = get_db()
    
    def generate_single(self, 
                       content: str,
                       output_path: str | Path,
                       size: int = None,
                       error_correction: str = 'L',
                       border: int = 1) -> Tuple[bool, str]:
        """Genera un código QR individual con configuración personalizada.
        
        Crea un código QR a partir del contenido proporcionado y lo guarda
        como imagen PNG. El tamaño se ajusta automáticamente si no se especifica.
        La operación se registra en la base de datos para auditoría.
        
        Args:
            content (str): Texto o datos a codificar en el QR. No debe estar vacío.
            output_path (str | Path): Ruta completa donde guardar el archivo QR.
                Se creará el directorio padre si no existe.
            size (int, optional): Tamaño del QR en píxeles (ancho y alto).
                Si es None, se calcula automáticamente. Defaults to None.
            error_correction (str, optional): Nivel de corrección de errores.
                Opciones:
                    - 'L': ~7% recuperable
                    - 'M': ~15% recuperable
                    - 'Q': ~25% recuperable
                    - 'H': ~30% recuperable (recomendado para QR con logo)
                Defaults to 'L'.
            border (int, optional): Grosor del borde blanco en cajas QR.
                Mínimo recomendado: 1. Defaults to 1.
            
        Returns:
            Tuple[bool, str]: Una tupla con:
                - bool: True si la generación fue exitosa, False en caso contrario
                - str: Ruta del archivo generado si exitoso, mensaje de error si falló
        
        Raises:
            No lanza excepciones directamente, pero captura y registra errores
            internos retornando (False, mensaje_error).
        
        Example:
            >>> generator = QRGenerator()
            >>> success, result = generator.generate_single(
            ...     content="https://github.com",
            ...     output_path="./output/github_qr.png",
            ...     size=500,
            ...     error_correction='H',
            ...     border=2
            ... )
            >>> if success:
            ...     print(f"QR guardado en: {result}")
            ... else:
            ...     print(f"Error: {result}")
        
        Note:
            - El contenido se trunca a 100 caracteres en los logs de base de datos
            - Los directorios intermedios se crean automáticamente
            - La imagen se genera con fondo blanco y código negro
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
        """Genera múltiples códigos QR en paralelo para optimizar el rendimiento.
        
        Procesa una lista de contenidos y genera códigos QR de forma paralela
        utilizando ThreadPoolExecutor. Los códigos QR se nombran automáticamente
        con un prefijo y un índice numérico. Las entradas vacías se filtran
        automáticamente.
        
        Args:
            contents (List[str]): Lista de textos o datos para codificar en QR.
                Los elementos vacíos o solo con espacios se ignoran automáticamente.
            output_folder (str | Path): Directorio donde guardar todos los QRs.
                Se crea automáticamente si no existe.
            size (int, optional): Tamaño de cada QR en píxeles. Si es None,
                se calcula automáticamente por cada QR. Defaults to None.
            prefix (str, optional): Prefijo para los nombres de archivo.
                Los archivos se nombrarán como "{prefix}{índice}.png".
                Defaults to "qr_".
            max_workers (int, optional): Número máximo de threads paralelos.
                Valores más altos aceleran la generación pero consumen más CPU.
                Defaults to 4.
            progress_callback (callable, optional): Función que se llama después
                de generar cada QR. Debe aceptar dos parámetros: (actual, total).
                Útil para actualizar barras de progreso. Defaults to None.
            
        Returns:
            Dict[int, str]: Diccionario mapeando índices originales a rutas de
                archivos generados exitosamente. Solo incluye QRs exitosos.
        
        Example:
            >>> generator = QRGenerator()
            >>> def progreso(actual, total):
            ...     print(f"Progreso: {actual}/{total}")
            >>> 
            >>> urls = ["url1", "url2", "url3", "", "url5"]  # url4 vacía
            >>> resultados = generator.generate_batch(
            ...     contents=urls,
            ...     output_folder="./batch_qrs/",
            ...     prefix="url_",
            ...     max_workers=2,
            ...     progress_callback=progreso
            ... )
            >>> print(f"Generados {len(resultados)} de {len(urls)} QRs")
        
        Note:
            - Las entradas vacías o None se filtran automáticamente
            - La operación completa se registra en la base de datos
            - Si algunos QRs fallan, el proceso continúa con los demás
            - El tiempo total de procesamiento se registra para estadísticas
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
        """Worker interno para generación paralela de QRs.
        
        Función ejecutada por cada thread en generate_batch. Genera un QR
        individual y retorna el resultado con su índice para mantener el orden.
        
        Args:
            args (tuple): Tupla de 4 elementos:
                - idx (int): Índice del QR en la lista original
                - content (str): Contenido a codificar
                - output_path (Path): Ruta completa de salida
                - size (int): Tamaño del QR en píxeles
            
        Returns:
            Tuple[int, str, bool]: Tupla con:
                - int: Índice original del QR
                - str: Ruta del archivo generado o None si falló
                - bool: True si la generación fue exitosa, False si falló
        
        Note:
            Este método es privado y no debe ser llamado directamente.
            Es utilizado internamente por generate_batch.
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
        """Genera un código QR con un logo personalizado en el centro.
        
        Crea un QR con nivel alto de corrección de errores ('H') y superpone
        una imagen de logo en el centro. El logo se redimensiona automáticamente
        al 20% del tamaño total del QR para mantener la legibilidad.
        
        Args:
            content (str): Texto o datos a codificar en el QR.
            output_path (str | Path): Ruta donde guardar el QR con logo.
            logo_path (str | Path): Ruta de la imagen del logo a insertar.
                Debe ser un archivo de imagen válido (PNG, JPG, etc.).
            size (int, optional): Tamaño final del QR en píxeles (ancho y alto).
                Defaults to 300.
            
        Returns:
            Tuple[bool, str]: Una tupla con:
                - bool: True si la generación fue exitosa, False en caso contrario
                - str: Ruta del archivo generado si exitoso, mensaje de error si falló
        
        Example:
            >>> generator = QRGenerator()
            >>> success, result = generator.generate_with_logo(
            ...     content="https://miempresa.com",
            ...     output_path="./qr_logo.png",
            ...     logo_path="./assets/logo.png",
            ...     size=500
            ... )
        
        Note:
            - Se usa corrección de errores nivel 'H' (30%) para compensar
              el área ocupada por el logo
            - El logo se redimensiona proporcionalmente al 20% del tamaño del QR
            - El logo se centra automáticamente en el QR
            - Asegúrese de que el logo no sea demasiado complejo para mantener
              la legibilidad del QR
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
