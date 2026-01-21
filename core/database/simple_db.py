"""
SGDI - Base de Datos Simple
============================

Módulo para gestión sencilla de base de datos SQLite.
Proporciona métodos CRUD básicos y manejo de conexiones.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from config.settings import Settings


class Database:
    """Clase para gestión de base de datos SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos. Si es None, usa Settings.DATABASE_PATH
        """
        self.db_path = db_path or Settings.DATABASE_PATH
        self.connection = None
        self.cursor = None
        
        # Asegurar que el directorio existe
        Settings.ensure_directories()
        
        # Inicializar base de datos si no existe
        if not os.path.exists(self.db_path):
            self._initialize_database()
    
    def connect(self):
        """Establece conexión con la base de datos."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
            self.cursor = self.connection.cursor()
    
    def disconnect(self):
        """Cierra la conexión con la base de datos."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def _initialize_database(self):
        """Inicializa la base de datos ejecutando el schema.sql"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema no encontrado: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        self.connect()
        self.cursor.executescript(schema_sql)
        self.connection.commit()
        print(f"✓ Base de datos inicializada: {self.db_path}")
    
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        Ejecuta una consulta SQL.
        
        Args:
            query: Consulta SQL
            params: Parámetros de la consulta
            
        Returns:
            Cursor con los resultados
        """
        self.connect()
        return self.cursor.execute(query, params)
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Ejecuta múltiples inserciones/actualizaciones.
        
        Args:
            query: Consulta SQL
            params_list: Lista de tuplas con parámetros
            
        Returns:
            Número de filas afectadas
        """
        self.connect()
        self.cursor.executemany(query, params_list)
        self.connection.commit()
        return self.cursor.rowcount
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Obtiene un solo registro.
        
        Args:
            query: Consulta SQL
            params: Parámetros de la consulta
            
        Returns:
            Diccionario con el registro o None
        """
        self.execute(query, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros.
        
        Args:
            query: Consulta SQL
            params: Parámetros de la consulta
            
        Returns:
            Lista de diccionarios con los registros
        """
        self.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Inserta un registro en una tabla.
        
        Args:
            table: Nombre de la tabla
            data: Diccionario con los datos a insertar
            
        Returns:
            ID del registro insertado
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        self.execute(query, tuple(data.values()))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: Tuple = ()) -> int:
        """
        Actualiza registros en una tabla.
        
        Args:
            table: Nombre de la tabla
            data: Diccionario con los datos a actualizar
            where: Cláusula WHERE
            where_params: Parámetros de la cláusula WHERE
            
        Returns:
            Número de filas afectadas
        """
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        params = tuple(data.values()) + where_params
        self.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: Tuple = ()) -> int:
        """
        Elimina registros de una tabla.
        
        Args:
            table: Nombre de la tabla
            where: Cláusula WHERE
            where_params: Parámetros de la cláusula WHERE
            
        Returns:
            Número de filas eliminadas
        """
        query = f"DELETE FROM {table} WHERE {where}"
        self.execute(query, where_params)
        self.connection.commit()
        return self.cursor.rowcount
    
    # ===================================
    # Métodos específicos para cada tabla
    # ===================================
    
    def log_to_database(self, module: str, action: str, level: str, message: str, 
                       traceback: str = None, extra_data: dict = None):
        """
        Registra un log en la base de datos.
        
        Args:
            module: Nombre del módulo
            action: Acción realizada
            level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Mensaje del log
            traceback: Traceback en caso de error
            extra_data: Datos adicionales en formato dict
        """
        data = {
            'module_name': module,
            'action': action,
            'level': level,
            'message': message,
            'traceback': traceback,
            'extra_data': json.dumps(extra_data) if extra_data else None
        }
        return self.insert('system_logs', data)
    
    def save_generated_code(self, code: str, article_name: str = "", 
                           meter_serial: str = "", service_type: str = "",
                           excel_path: str = None, notes: str = None) -> int:
        """Guarda un código generado con columnas separadas."""
        data = {
            'code': code,
            'article_name': article_name,
            'meter_serial': meter_serial,
            'service_type': service_type,
            'exported_to_excel': 1 if excel_path else 0,
            'excel_export_path': excel_path,
            'notes': notes
        }
        return self.insert('generated_codes', data)
    
    def code_exists(self, code: str) -> bool:
        """Verifica si un código ya existe."""
        result = self.fetch_one(
            "SELECT COUNT(*) as count FROM generated_codes WHERE code = ?",
            (code,)
        )
        return result['count'] > 0 if result else False
    
    def get_all_codes(self) -> set:
        """Obtiene todos los códigos generados."""
        rows = self.fetch_all("SELECT code FROM generated_codes")
        return {row['code'] for row in rows}
    
    def save_qr_operation(self, operation_type: str, status: str, 
                         file_path: str = None, qr_content: str = None,
                         items_processed: int = 0, duration: float = 0,
                         error_message: str = None) -> int:
        """Guarda una operación de QR."""
        data = {
            'operation_type': operation_type,
            'file_path': file_path,
            'qr_content': qr_content,
            'status': status,
            'error_message': error_message,
            'items_processed': items_processed,
            'duration_seconds': duration
        }
        return self.insert('qr_operations', data)
    
    def save_file_audit(self, folder_path: str, total_expected: int, total_found: int,
                       missing_count: int, extra_count: int, report_path: str = None,
                       audit_type: str = 'general') -> int:
        """Guarda un resultado de auditoría."""
        data = {
            'folder_path': folder_path,
            'total_expected': total_expected,
            'total_found': total_found,
            'missing_count': missing_count,
            'extra_count': extra_count,
            'report_path': report_path,
            'audit_type': audit_type
        }
        return self.insert('file_audits', data)
    
    def save_pdf_compression(self, folder_path: str, files_processed: int,
                            original_size_mb: float, compressed_size_mb: float,
                            space_saved_mb: float, duration: float,
                            files_skipped: int = 0, files_error: int = 0,
                            compression_quality: int = 70) -> int:
        """Guarda una operación de compresión PDF."""
        data = {
            'folder_path': folder_path,
            'files_processed': files_processed,
            'files_skipped': files_skipped,
            'files_error': files_error,
            'original_size_mb': original_size_mb,
            'compressed_size_mb': compressed_size_mb,
            'space_saved_mb': space_saved_mb,
            'compression_ratio': (space_saved_mb / original_size_mb * 100) if original_size_mb > 0 else 0,
            'compression_quality': compression_quality,
            'duration_seconds': duration
        }
        return self.insert('pdf_compressions', data)
    
    def save_file_search(self, source_path: str, destination_path: str,
                        files_searched: int, files_found: int, files_copied: int,
                        duration: float, files_error: int = 0, search_pattern: str = None) -> int:
        """Guarda una operación de búsqueda de archivos."""
        data = {
            'source_path': source_path,
            'destination_path': destination_path,
            'files_searched': files_searched,
            'files_found': files_found,
            'files_copied': files_copied,
            'files_error': files_error,
            'search_pattern': search_pattern,
            'duration_seconds': duration
        }
        return self.insert('file_searches', data)
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas para el dashboard."""
        return self.fetch_one("SELECT * FROM v_dashboard_stats") or {}
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene los logs más recientes."""
        return self.fetch_all(
            f"SELECT * FROM v_recent_logs LIMIT ?",
            (limit,)
        )
    
    def __enter__(self):
        """Context manager: entrada."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: salida."""
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.disconnect()


# Instancia global para uso compartido
_db_instance = None

def get_db() -> Database:
    """Obtiene la instancia global de la base de datos."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
