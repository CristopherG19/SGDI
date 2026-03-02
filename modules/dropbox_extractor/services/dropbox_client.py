"""
SGDI - Dropbox Client
=====================

Cliente para interactuar con la API de Dropbox.
Maneja autenticación con OAuth 2.0 Refresh Token, listado de archivos y generación de URLs compartidas.
"""

import dropbox
from dropbox.exceptions import AuthError, ApiError
from typing import List, Dict, Optional, Callable
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

from core.utils.logger import get_logger

log = get_logger(__name__)


class DropboxClient:
    """Cliente para interactuar con la API de Dropbox con OAuth 2.0."""
    
    def __init__(self, refresh_token: str, app_key: str, app_secret: str):
        """
        Inicializa el cliente de Dropbox con OAuth 2.0.
        
        Args:
            refresh_token: Refresh token de OAuth para generar access tokens
            app_key: App Key de Dropbox
            app_secret: App Secret de Dropbox
        """
        self.refresh_token = refresh_token
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
        self.token_expiry = None
        self.dbx = None
        self._connected = False
    
    def _refresh_access_token(self) -> bool:
        """
        Genera un nuevo access token usando el refresh token.
        Los access tokens de Dropbox expiran cada ~4 horas.
        
        Returns:
            bool: True si se generó exitosamente
        """
        try:
            log.info("Generando nuevo access token...")
            
            url = "https://api.dropbox.com/oauth2/token"
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.app_key,
                'client_secret': self.app_secret
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result['access_token']
                # Los tokens expiran en aproximadamente 4 horas
                self.token_expiry = datetime.now() + timedelta(hours=4)
                
                log.info("✅ Access token generado exitosamente")
                log.debug(f"Token expirará aproximadamente a las {self.token_expiry.strftime('%H:%M:%S')}")
                return True
            else:
                log.error(f"Error al generar access token: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log.error(f"Excepción al generar access token: {e}")
            return False
    
    def _ensure_valid_token(self) -> bool:
        """
        Asegura que tenemos un access token válido.
        Si no existe o está por expirar, genera uno nuevo.
        
        Returns:
            bool: True si hay un token válido disponible
        """
        # Si no hay token o está por expirar en menos de 5 minutos, renovar
        if (self.access_token is None or 
            self.token_expiry is None or 
            datetime.now() >= (self.token_expiry - timedelta(minutes=5))):
            
            return self._refresh_access_token()
        
        return True
        
    def connect(self) -> bool:
        """
        Establece conexión con Dropbox generando access token y validándolo.
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            # Generar access token desde refresh token
            if not self._refresh_access_token():
                log.error("No se pudo generar access token")
                self._connected = False
                return False
            
            # Crear cliente de Dropbox con el access token
            self.dbx = dropbox.Dropbox(self.access_token)
            
            # Verificar que el token es válido
            account = self.dbx.users_get_current_account()
            self._connected = True
            log.info(f"✅ Conectado a Dropbox como: {account.name.display_name}")
            log.info(f"📧 Email: {account.email}")
            return True
            
        except AuthError as e:
            log.error(f"Error de autenticación: {e}")
            self._connected = False
            return False
        except Exception as e:
            log.error(f"Error al conectar a Dropbox: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Retorna si hay una conexión activa."""
        return self._connected
    
    def list_folders(self, path: str = "") -> List[Dict]:
        """
        Lista carpetas en una ruta específica.
        
        Args:
            path: Ruta en Dropbox (vacío para raíz)
            
        Returns:
            Lista de diccionarios con información de carpetas
        """
        if not self._connected:
            log.error("No hay conexión activa con Dropbox")
            return []
        
        # Asegurar que el token es válido
        if not self._ensure_valid_token():
            log.error("No se pudo obtener un token válido")
            return []
        
        folders = []
        try:
            result = self.dbx.files_list_folder(path)
            
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FolderMetadata):
                    folders.append({
                        'name': entry.name,
                        'path': entry.path_display,
                        'id': entry.id
                    })
            
            log.info(f"Encontradas {len(folders)} carpetas en {path or 'raíz'}")
            return folders
            
        except ApiError as e:
            log.error(f"Error al listar carpetas: {e}")
            return []
    
    def find_folders(self, query: str, root_path: str = "") -> List[Dict]:
        """
        Busca carpetas que coincidan con el nombre (query).
        Optimiza la búsqueda evitando escanear todo el árbol.
        
        Args:
            query: Nombre o parte del nombre de carpeta a buscar
            root_path: Ruta raíz donde buscar (ej: /INACAL)
            
        Returns:
            Lista de carpetas encontradas
        """
        if not self._connected:
            log.error("No hay conexión activa con Dropbox")
            return []
            
        if not self._ensure_valid_token():
            log.error("No se pudo obtener un token válido")
            return []
            
        folders = []
        query_upper = query.upper()
        
        try:
            # Estrategia: Listar subcarpetas de las rutas conocidas
            # Estructura esperada: /INACAL/VERIFICACION INICIAL/[CARPETAS_FECHA]
            search_paths = []
            
            if root_path:
                search_paths.append(root_path)
                # Agregar rutas conocidas de INACAL
                search_paths.append(f"{root_path}/VERIFICACION INICIAL")
                search_paths.append(f"{root_path}/VERIFICACION POSTERIOR")
            else:
                search_paths = ["", "/INACAL", "/INACAL/VERIFICACION INICIAL", "/INACAL/VERIFICACION POSTERIOR"]
            
            for path in search_paths:
                try:
                    log.debug(f"Buscando en: {path}")
                    result = self.dbx.files_list_folder(path)
                    
                    while True:
                        for entry in result.entries:
                            if isinstance(entry, dropbox.files.FolderMetadata):
                                # Comparar nombre de carpeta con query
                                if query_upper in entry.name.upper():
                                    folders.append({
                                        'name': entry.name,
                                        'path': entry.path_display,
                                        'id': entry.id
                                    })
                                    log.info(f"✅ Carpeta encontrada: {entry.path_display}")
                        
                        if not result.has_more:
                            break
                        result = self.dbx.files_list_folder_continue(result.cursor)
                        
                except ApiError as e:
                    # Ruta no existe, continuar con la siguiente
                    log.debug(f"Ruta no accesible: {path} - {e}")
                    continue
            
            log.info(f"🔍 Búsqueda completada: {len(folders)} carpetas coinciden con '{query}'")
            return folders
            
        except Exception as e:
            log.error(f"Error en búsqueda de carpetas: {e}")
            return []
    
    def list_files_recursive(
        self, 
        path: str, 
        filters: Dict = None,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Lista archivos recursivamente en una ruta.
        
        Args:
            path: Ruta inicial en Dropbox
            filters: Filtros a aplicar (tipo, fecha, patrón)
            progress_callback: Función callback para reporte de progreso
            
        Returns:
            Lista de diccionarios con información de archivos
        """
        if not self._connected:
            log.error("No hay conexión activa con Dropbox")
            return []
        
        # Asegurar que el token es válido
        if not self._ensure_valid_token():
            log.error("No se pudo obtener un token válido")
            return []
        
        filters = filters or {}
        all_files = []
        processed_count = 0
        
        try:
            result = self.dbx.files_list_folder(path, recursive=True)
            
            while True:
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        file_info = {
                            'name': entry.name,
                            'path': entry.path_display,
                            'id': entry.id,
                            'size': entry.size,
                            'modified': entry.server_modified.isoformat() if entry.server_modified else None,
                            'parent_folder': str(Path(entry.path_display).parent)
                        }
                        
                        # Aplicar filtros
                        if self._apply_filters(file_info, filters):
                            all_files.append(file_info)
                        
                        processed_count += 1
                        
                        # Reportar progreso
                        if progress_callback and processed_count % 10 == 0:
                            progress_callback(processed_count, len(all_files), {'status': 'scanning'})
                
                # Obtener siguiente página de resultados
                if not result.has_more:
                    break
                result = self.dbx.files_list_folder_continue(result.cursor)
            
            log.info(f"Encontrados {len(all_files)} archivos (procesados {processed_count})")
            return all_files
            
        except ApiError as e:
            log.error(f"Error al listar archivos: {e}")
            return all_files
    
    def _apply_filters(self, file_info: Dict, filters: Dict) -> bool:
        """
        Aplica filtros a un archivo.
        
        Args:
            file_info: Información del archivo
            filters: Diccionario de filtros
            
        Returns:
            bool: True si el archivo pasa los filtros
        """
        # Filtro por tipo de verificación (carpeta padre)
        folder_types = filters.get('folder_types', [])
        if folder_types:
            parent_folder = file_info['parent_folder'].upper()
            if not any(ftype in parent_folder for ftype in folder_types):
                return False
        
        # Filtro por patrón de nombre de carpeta
        folder_pattern = filters.get('folder_pattern', '').upper()
        if folder_pattern:
            parent_folder = file_info['parent_folder'].upper()
            # Extraer nombre de la carpeta final
            folder_name = Path(parent_folder).name
            if folder_pattern not in folder_name:
                return False
        
        # Filtro por rango de fechas
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        
        if (date_from or date_to) and file_info['modified']:
            file_date = datetime.fromisoformat(file_info['modified']).date()
            
            if date_from and file_date < date_from:
                return False
            if date_to and file_date > date_to:
                return False
        
        return True
    
    def get_all_shared_links(self) -> Dict[str, str]:
        """
        Obtiene TODOS los enlaces compartidos existentes de una sola vez.
        OPTIMIZACIÓN CRUCIAL: Reduce llamadas API de N a 1.
        
        Returns:
            Diccionario {path_lower: url} con todos los enlaces existentes
        """
        if not self._connected:
            log.error("No hay conexión activa con Dropbox")
            return {}
        
        # Asegurar token válido
        if not self._ensure_valid_token():
            log.error("No se pudo obtener un token válido")
            return {}
        
        try:
            log.info("📥 Cargando todos los enlaces compartidos...")
            enlaces = {}
            result = self.dbx.sharing_list_shared_links()
            
            for link in result.links:
                enlaces[link.path_lower] = link.url
            
            # Manejar paginación si hay muchos enlaces
            while result.has_more:
                result = self.dbx.sharing_list_shared_links(cursor=result.cursor)
                for link in result.links:
                    enlaces[link.path_lower] = link.url
            
            log.info(f"✅ Enlaces compartidos cargados: {len(enlaces)}")
            return enlaces
            
        except Exception as e:
            log.error(f"Error al obtener enlaces compartidos: {e}")
            return {}
    
    def create_shared_link(self, file_path: str, shared_links_cache: Dict[str, str] = None, rate_limit_pause: float = 0.1) -> Optional[str]:
        """
        Crea o obtiene un link compartido para un archivo.
        OPTIMIZADO: Usa cache de enlaces pre-cargados.
        
        Args:
            file_path: Ruta del archivo en Dropbox
            shared_links_cache: Cache de enlaces {path_lower: url}
            rate_limit_pause: Pausa en segundos (reducido a 0.1 con cache)
            
        Returns:
            URL compartida o None si hay error
        """
        if not self._connected:
            return None
        
        # Asegurar token válido
        if not self._ensure_valid_token():
            return None
        
        try:
            # 1. PRIMERO: Verificar en cache (mucho más rápido)
            path_lower = file_path.lower()
            if shared_links_cache and path_lower in shared_links_cache:
                url = shared_links_cache[path_lower]
                return url.replace('?dl=0', '?dl=1')
            
            # 2. Si no está en cache, crear nuevo link
            link_metadata = self.dbx.sharing_create_shared_link_with_settings(file_path)
            url = link_metadata.url.replace('?dl=0', '?dl=1')
            
            # 3. Agregar al cache para futuras consultas
            if shared_links_cache is not None:
                shared_links_cache[path_lower] = url
            
            # Pausa mínima (ya casi no es necesaria con el cache)
            time.sleep(rate_limit_pause)
            return url
            
        except ApiError as e:
            # Error 409: Link ya existe (race condition)
            if hasattr(e.error, 'get_shared_link_already_exists'):
                try:
                    links = self.dbx.sharing_list_shared_links(path=file_path, direct_only=True)
                    if links.links:
                        url = links.links[0].url.replace('?dl=0', '?dl=1')
                        if shared_links_cache is not None:
                            shared_links_cache[path_lower] = url
                        return url
                except Exception as e2:
                    log.error(f"❌ Error obteniendo link existente para {file_path}: {e2}")
            
            log.error(f"❌ ApiError al crear link para {file_path}: {e}")
            return None
        except Exception as e:
            log.error(f"❌ Error inesperado al crear link para {file_path}: {e}")
            return None
    
    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        """
        Obtiene metadata de un archivo.
        
        Args:
            file_path: Ruta del archivo en Dropbox
            
        Returns:
            Diccionario con metadata o None si hay error
        """
        if not self._connected:
            log.error("No hay conexión activa con Dropbox")
            return None
        
        # Asegurar que el token es válido
        if not self._ensure_valid_token():
            log.error("No se pudo obtener un token válido")
            return None
        
        try:
            metadata = self.dbx.files_get_metadata(file_path)
            
            if isinstance(metadata, dropbox.files.FileMetadata):
                return {
                    'name': metadata.name,
                    'path': metadata.path_display,
                    'size': metadata.size,
                    'modified': metadata.server_modified.isoformat() if metadata.server_modified else None,
                    'id': metadata.id
                }
            
            return None
            
        except ApiError as e:
            log.error(f"Error al obtener metadata: {e}")
            return None
