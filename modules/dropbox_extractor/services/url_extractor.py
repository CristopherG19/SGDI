"""
SGDI - URL Extractor Service
=============================

Servicio para extraer URLs de archivos en Dropbox de forma masiva.
"""

from typing import List, Dict, Optional, Callable
from datetime import datetime
from pathlib import Path

from modules.dropbox_extractor.services.dropbox_client import DropboxClient
from core.utils.logger import get_logger

log = get_logger(__name__)


class URLExtractor:
    """Servicio para extraer URLs de archivos en Dropbox."""
    
    def __init__(self, dropbox_client: DropboxClient):
        """
        Inicializa el extractor.
        
        Args:
            dropbox_client: Cliente de Dropbox configurado
        """
        self.client = dropbox_client
        self.stop_flag = False
        self.stats = {
            'total_found': 0,
            'urls_extracted': 0,
            'errors': 0,
            'cached': 0,
            'start_time': None,
            'end_time': None
        }
    
    def extract_urls(
        self,
        config: Dict,
        progress_callback: Optional[Callable] = None,
        url_cache: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Extrae URLs de archivos según configuración.
        
        Args:
            config: Configuración de extracción con filtros
                - root_path: Ruta raíz en Dropbox
                - folder_types: Lista de tipos ['INICIAL', 'POSTERIOR']
                - folder_pattern: Patrón de nombre de carpeta
                - date_from: Fecha desde (datetime.date)
                - date_to: Fecha hasta (datetime.date)
                - rate_limit_pause: Pausa entre requests (float)
            progress_callback: Función callback(current, total, file_info)
            url_cache: Diccionario {file_path: url} para cache
            
        Returns:
            Lista de diccionarios con información de archivos y URLs
        """
        self.stop_flag = False
        self.stats = {
            'total_found': 0,
            'urls_extracted': 0,
            'errors': 0,
            'cached': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        url_cache = url_cache or {}
        results = []
        
        try:
            # Paso 1: Listar archivos con filtros
            log.info("Iniciando búsqueda de archivos...")
            filters = {
                'folder_types': config.get('folder_types', []),
                'folder_pattern': config.get('folder_pattern', ''),
                'date_from': config.get('date_from'),
                'date_to': config.get('date_to')
            }
            # Paso 1: Obtener lista de archivos
            log.info("Iniciando extracción...")
            folder_path = config.get('root_path', '')
            
            # Filtros
            folder_pattern = config.get('folder_pattern', '')
            target_files = []
            
            # DEBUG: Log para diagnóstico
            log.info(f"📋 DEBUG: folder_path='{folder_path}', folder_pattern='{folder_pattern}', len={len(folder_pattern)}")
            
            # ESTRATEGIA OPTIMIZADA: Si hay patrón de carpeta, BUSCAR solo esa carpeta
            if folder_pattern and len(folder_pattern) > 3:
                log.info(f"⚡ Estrategia optimizada de búsqueda para: '{folder_pattern}'")
                
                # Buscar carpetas que coincidan
                matching_folders = self.client.find_folders(folder_pattern, folder_path)
                log.info(f"📋 DEBUG: find_folders retornó {len(matching_folders)} carpetas")
                
                if matching_folders:
                    for folder in matching_folders:
                        log.info(f"📂 Escaneando contenido de: {folder['path']}")
                        # Escanear SOLO esta carpeta
                        # Pass the 'filters' dictionary, not the whole 'config'
                        files = self.client.list_files_recursive(folder['path'], filters=filters, progress_callback=progress_callback)
                        target_files.extend(files)
                    
                    files = target_files # Reemplazar lista completa con la filtrada
                else:
                    log.warning(f"⚠️ No se encontraron carpetas con el patrón '{folder_pattern}'. Escaneando todo (lento)...")
                    # Pass the 'filters' dictionary, not the whole 'config'
                    files = self.client.list_files_recursive(folder_path, filters=filters, progress_callback=progress_callback)
            else:
                # Estrategia original (lenta para muchos archivos)
                log.info("🐌 Escaneando todo el directorio (sin patrón específico)...")
                # Pass the 'filters' dictionary, not the whole 'config'
                files = self.client.list_files_recursive(folder_path, filters=filters, progress_callback=progress_callback)
            
            self.stats['total_found'] = len(files) # Moved this line here
            log.info(f"✅ Archivos encontrados para procesar: {len(files)}")
            
            if not files:
                log.warning("No se encontraron archivos con los filtros especificados")
                return results
            
            # Paso 2: PRE-CARGAR ENLACES COMPARTIDOS (con límite inteligente)
            log.info("📥 Cargando enlaces compartidos existentes...")
            shared_links_cache = {}
            
            # OPTIMIZACIÓN: Si tenemos pocos archivos (<= 1000), NO pre-cargar todo el cache
            # Es más rápido crear los enlaces bajo demanda
            skip_precache = len(files) <= 1000
            
            if skip_precache:
                log.info(f"⚡ Saltando pre-cache (solo {len(files)} archivos - será más rápido bajo demanda)")
            else:
                try:
                    result = self.client.dbx.sharing_list_shared_links()
                    for link in result.links:
                        shared_links_cache[link.path_lower] = link.url
                    
                    # Limitar a 10 páginas máximo (10,000 enlaces) para no tardar tanto
                    page_count = 1
                    MAX_PAGES = 10  # Reducido de 200 a 10
                    while result.has_more and page_count < MAX_PAGES:
                        result = self.client.dbx.sharing_list_shared_links(cursor=result.cursor)
                        for link in result.links:
                            shared_links_cache[link.path_lower] = link.url
                        page_count += 1
                        log.info(f"📥 Pre-cargando cache: página {page_count}/{MAX_PAGES}...")
                    
                    log.info(f"✅ Cache cargado con {len(shared_links_cache)} enlaces")
                except Exception as e:
                    log.warning(f"No se pudo pre-cargar enlaces: {e}. Continuando sin pre-cache...")
                    shared_links_cache = {}
            
            # Paso 3: Generar URLs - MODO RÁPIDO
            rate_pause = 0.05  # 50ms entre llamadas
            max_workers = 15   # 15 threads paralelos (~25-30 URLs/seg)
            
            log.info(f"🚀 Iniciando extracción paralela con {max_workers} workers...")
            
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def process_file(file_info):
                """Procesa un archivo individual (se ejecuta en paralelo)"""
                if self.stop_flag:
                    return None
                
                file_path = file_info['path']
                url = None
                
                # 1. Verificar cache local (BD)
                if file_path in url_cache:
                    url = url_cache[file_path]
                    self.stats['cached'] += 1
                else:
                    # 2. Generar URL (con cache compartido)
                    url = self.client.create_shared_link(file_path, shared_links_cache, rate_pause)
                    
                    if url:
                        self.stats['urls_extracted'] += 1
                        url_cache[file_path] = url
                    else:
                        self.stats['errors'] += 1
                
                # Crear resultado
                if url:
                    return {
                        **file_info,
                        'url': url,
                        'folder_type': self._get_folder_type(file_info['parent_folder']),
                        'extraction_date': datetime.now().isoformat()
                    }
                return None
            
            # Procesar archivos en paralelo
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Enviar todos los archivos para procesamiento
                futures = {executor.submit(process_file, file_info): idx 
                          for idx, file_info in enumerate(files)}
                
                # Recoger resultados conforme se completan
                for future in as_completed(futures):
                    if self.stop_flag:
                        log.info("Extracción detenida por usuario")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    idx = futures[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        log.error(f"Error procesando archivo {idx}: {e}")
                        self.stats['errors'] += 1
                    
                    # Reportar progreso
                    if progress_callback and idx % 10 == 0:  # Cada 10 archivos
                        progress_callback(len(results), len(files), {
                            'status': 'extracting',
                            'file': files[idx]['name'] if idx < len(files) else '',
                            'urls_extracted': len(results),
                            'errors': self.stats['errors']
                        })
            
            self.stats['end_time'] = datetime.now()
            log.info(f"Extracción completada: {len(results)} URLs generadas")
            
            return results
            
        except Exception as e:
            log.error(f"Error durante la extracción: {e}")
            self.stats['end_time'] = datetime.now()
            return results
    
    def _get_folder_type(self, parent_folder: str) -> str:
        """
        Determina el tipo de verificación según la carpeta padre.
        
        Args:
            parent_folder: Ruta de la carpeta padre
            
        Returns:
            'INICIAL', 'POSTERIOR' o 'DESCONOCIDO'
        """
        folder_upper = parent_folder.upper()
        
        if 'INICIAL' in folder_upper:
            return 'INICIAL'
        elif 'POSTERIOR' in folder_upper:
            return 'POSTERIOR'
        else:
            return 'DESCONOCIDO'
    
    def stop_extraction(self):
        """Detiene la extracción en curso."""
        self.stop_flag = True
        log.info("Solicitud de detención recibida")
    
    def get_extraction_stats(self) -> Dict:
        """
        Obtiene estadísticas de la última extracción.
        
        Returns:
            Diccionario con estadísticas
        """
        stats = self.stats.copy()
        
        # Calcular duración si está disponible
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            stats['duration_seconds'] = duration.total_seconds()
            
            # Calcular velocidad
            if stats['duration_seconds'] > 0:
                stats['files_per_second'] = stats['urls_extracted'] / stats['duration_seconds']
        
        return stats
    
    def apply_filters(self, files: List[Dict], config: Dict) -> List[Dict]:
        """
        Aplica filtros adicionales a una lista de archivos.
        
        Args:
            files: Lista de archivos
            config: Configuración de filtros
            
        Returns:
            Lista filtrada
        """
        filtered = []
        
        for file_info in files:
            # Filtro por tipo de carpeta
            folder_types = config.get('folder_types', [])
            if folder_types:
                folder_type = self._get_folder_type(file_info.get('parent_folder', ''))
                if folder_type not in folder_types:
                    continue
            
            # Filtro por patrón de nombre
            pattern = config.get('folder_pattern', '').upper()
            if pattern:
                parent_name = Path(file_info.get('parent_folder', '')).name.upper()
                if pattern not in parent_name:
                    continue
            
            # Filtro por fecha
            date_from = config.get('date_from')
            date_to = config.get('date_to')
            
            if (date_from or date_to) and file_info.get('modified'):
                try:
                    file_date = datetime.fromisoformat(file_info['modified']).date()
                    
                    if date_from and file_date < date_from:
                        continue
                    if date_to and file_date > date_to:
                        continue
                except:
                    pass
            
            filtered.append(file_info)
        
        return filtered
