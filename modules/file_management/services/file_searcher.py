"""
SGDI - Servicio de Búsqueda de Archivos
========================================

Búsqueda paralela de archivos en carpetas locales y de red.
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Callable, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from core.utils.logger import get_logger, log_operation
from core.database.simple_db import get_db

log = get_logger(__name__)


class FileSearcher:
    """Buscador de archivos con procesamiento paralelo."""
    
    def __init__(self):
        """Inicializa el buscador."""
        self.stop_requested = False
    
    def stop(self):
        """Detiene la búsqueda."""
        self.stop_requested = True
        log.info("Deteniendo búsqueda de archivos...")
    
    def search_and_copy(self,
                       source_path: str | Path,
                       file_names: List[str],
                       destination_path: str | Path,
                       progress_callback: Optional[Callable] = None) -> Dict:
        """
        Busca archivos y los copia al destino.
        
        Args:
            source_path: Carpeta origen (puede ser ruta de red)
            file_names: Lista de nombres a buscar
            destination_path: Carpeta destino
            progress_callback: Función(current, total, mensaje)
            
        Returns:
            Diccionario con estadísticas
        """
        self.stop_requested = False
        stats = {
            "searched": 0,
            "found": 0,
            "copied": 0,
            "errors": 0,
            "not_found": [],
            "error_details": [],  # Lista de errores detallados
            "duplicate_files": {}  # {nombre_archivo: cantidad_encontrada}
        }
        
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            # Validar rutas
            if not source.exists():
                log.error(f"Ruta origen no existe: {source}")
                return stats
            
            destination.mkdir(parents=True, exist_ok=True)
            
            log.info(f"Iniciando búsqueda en: {source}")
            log.info(f"Buscando {len(file_names)} archivos")
            
            # Obtener subdirectorios
            if progress_callback:
                progress_callback(0, 1, "Escaneando directorios...")
            
            subdirs = self._get_subdirectories(source)
            total_dirs = len(subdirs)
            
            log.info(f"Encontrados {total_dirs} subdirectorios")
            
            # Archivos a buscar
            search_set = set(file_names)
            found_files: Dict[str, List[Path]] = {name: [] for name in search_set}
            
            # Búsqueda paralela
            num_workers = (os.cpu_count() or 4) * 2
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [
                    executor.submit(self._search_in_directory, subdir, search_set)
                    for subdir in subdirs
                ]
                
                for idx, future in enumerate(as_completed(futures), 1):
                    if self.stop_requested:
                        log.warning("Búsqueda detenida por usuario")
                        break
                    
                    stats["searched"] += 1
                    
                    if progress_callback:
                        progress_callback(idx, total_dirs, f"Escaneando {idx}/{total_dirs}")
                    
                    # Procesar resultados
                    for file_name, file_path in future.result():
                        found_files[file_name].append(file_path)
            
            # Copiar archivos encontrados
            for file_name, paths in found_files.items():
                if paths:
                    stats["found"] += len(paths)
                    
                    # Registrar duplicados si se encontró más de una vez
                    if len(paths) > 1:
                        stats["duplicate_files"][file_name] = len(paths)
                        log.warning(f"Archivo '{file_name}' encontrado {len(paths)} veces")
                    
                    for idx, src_path in enumerate(paths):
                        if self.stop_requested:
                            break
                        
                        try:
                            dest_file = destination / src_path.name
                            
                            # Si es duplicado, agregar sufijo
                            if idx > 0:
                                stem = src_path.stem
                                suffix = src_path.suffix
                                dest_file = destination / f"{stem}_copia{idx}{suffix}"
                            
                            shutil.copy2(src_path, dest_file)
                            stats["copied"] += 1
                            log.info(f"Copiado: {src_path.name} -> {dest_file.name}")
                            
                        except Exception as e:
                            stats["errors"] += 1
                            
                            # Capturar detalles del error
                            error_info = {
                                "file_name": src_path.name,
                                "search_name": file_name,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "source_path": str(src_path),
                                "destination_path": str(dest_file),
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            stats["error_details"].append(error_info)
                            
                            log.error(f"Error copiando {src_path.name}: [{type(e).__name__}] {e}")
                            log.error(f"  Origen: {src_path}")
                            log.error(f"  Destino: {dest_file}")
                else:
                    stats["not_found"].append(file_name)
            
            # Registrar operación
            log_operation(
                module="file_searcher",
                action="search_and_copy",
                success=stats["errors"] == 0,
                message=f"Copiados {stats['copied']} de {len(file_names)} archivos",
                total=len(file_names),
                found=stats["found"],
                copied=stats["copied"],
                errors=stats["errors"]
            )
            
            # Guardar en BD (crear conexión en este thread)
            try:
                db = get_db()
                db.save_file_search(
                    source_path=str(source),
                    destination_path=str(destination),
                    files_searched=len(file_names),
                    files_found=stats["found"],
                    files_copied=stats["copied"],
                    files_error=stats["errors"],
                    duration=0,  # Se calculará después
                    search_pattern=", ".join(file_names[:5])
                )
                log.info("Búsqueda guardada en BD exitosamente")
            except Exception as db_error:
                # Error de BD no debe afectar el resultado de la búsqueda
                log.warning(f"No se pudo guardar en BD: [{type(db_error).__name__}] {db_error}")
                log.warning("Los archivos fueron copiados correctamente, solo falló el registro en BD")
            
        except Exception as e:
            log.error(f"Error en búsqueda: [{type(e).__name__}] {e}")
            stats["errors"] += 1
            
            # Capturar detalles del error general (BD, permisos, etc.)
            error_info = {
                "file_name": "N/A (Error general del sistema)",
                "search_name": "N/A",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "source_path": str(source_path),
                "destination_path": str(destination_path),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            stats["error_details"].append(error_info)
        
        return stats
    
    def _get_subdirectories(self, root: Path) -> List[Path]:
        """
        Obtiene todos los subdirectorios.
        
        Args:
            root: Directorio raíz
            
        Returns:
            Lista de paths de subdirectorios
        """
        subdirs = [root]
        
        try:
            for dirpath, _, _ in os.walk(root):
                if self.stop_requested:
                    break
                subdirs.append(Path(dirpath))
        except Exception as e:
            log.warning(f"Error escaneando subdirectorios: {e}")
        
        return subdirs
    
    def _search_in_directory(self, 
                            directory: Path,
                            search_set: Set[str]) -> List[Tuple[str, Path]]:
        """
        Busca archivos en un directorio.
        
        Args:
            directory: Directorio a buscar
            search_set: Set de nombres a buscar
            
        Returns:
            Lista de tuplas (nombre_buscado, path_encontrado)
        """
        found = []
        
        try:
            for item in os.listdir(directory):
                for search_name in search_set:
                    # Búsqueda por prefijo
                    if item.startswith(search_name):
                        full_path = directory / item
                        if full_path.is_file():
                            found.append((search_name, full_path))
        except (OSError, PermissionError):
            # Ignorar errores de permisos
            pass
        
        return found
    
    def search_files(self,
                    source_path: str | Path,
                    file_names: List[str],
                    progress_callback: Optional[Callable] = None) -> Dict[str, List[Path]]:
        """
        Solo busca archivos sin copiar.
        
        Args:
            source_path: Carpeta origen
            file_names: Lista de nombres
            progress_callback: Callback de progreso
            
        Returns:
            Diccionario {nombre: [paths encontrados]}
        """
        self.stop_requested = False
        source = Path(source_path)
        
        if not source.exists():
            log.error(f"Ruta no existe: {source}")
            return {}
        
        search_set = set(file_names)
        found_files: Dict[str, List[Path]] = {name: [] for name in search_set}
        
        # Obtener subdirectorios
        subdirs = self._get_subdirectories(source)
        total_dirs = len(subdirs)
        
        # Búsqueda paralela
        num_workers = (os.cpu_count() or 4) * 2
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(self._search_in_directory, subdir, search_set)
                for subdir in subdirs
            ]
            
            for idx, future in enumerate(as_completed(futures), 1):
                if self.stop_requested:
                    break
                
                if progress_callback:
                    progress_callback(idx, total_dirs, f"Buscando {idx}/{total_dirs}")
                
                for file_name, file_path in future.result():
                    found_files[file_name].append(file_path)
        
        return found_files
