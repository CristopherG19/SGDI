"""
SGDI - Analizador de Estadísticas
==================================

Servicio para obtener estadísticas y métricas del sistema.
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from core.utils.logger import get_logger
from core.database.simple_db import get_db

log = get_logger(__name__)


class StatsAnalyzer:
    """Analizador de estadísticas del sistema."""
    
    def __init__(self):
        """Inicializa el analizador."""
        self.db = get_db()
    
    def get_qr_stats(self, days: int = 30) -> Dict:
        """
        Obtiene estadísticas de operaciones QR.
        
        Args:
            days: Días hacia atrás
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            # Total de operaciones QR
            total = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM qr_operations"
            )
            
            # Por fecha (últimos días)
            date_limit = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            by_date = self.db.fetch_all(
                """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM qr_operations
                WHERE created_at >= %s
                GROUP BY DATE(created_at)
                ORDER BY date
                """,
                (date_limit,)
            )
            
            return {
                "total": total['count'] if total else 0,
                "by_date": by_date or [],
                "last_30_days": sum(r['count'] for r in by_date) if by_date else 0
            }
        except Exception as e:
            log.error(f"Error obteniendo stats de QR: {e}")
            return {"total": 0, "by_date": [], "last_30_days": 0}
    
    def get_codes_stats(self) -> Dict:
        """
        Estadísticas de códigos INACAL.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            # Total
            total = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM generated_codes"
            )
            
            # Por tipo de servicio
            by_type = self.db.fetch_all(
                """
                SELECT service_type, COUNT(*) as count
                FROM generated_codes
                WHERE service_type IS NOT NULL AND service_type != ''
                GROUP BY service_type
                """
            )
            
            # Recientes (últimos 7 días)
            recent = self.db.fetch_one(
                """
                SELECT COUNT(*) as count
                FROM generated_codes
                WHERE created_at >= NOW() - INTERVAL 7 DAY
                """
            )
            
            return {
                "total": total['count'] if total else 0,
                "by_type": {r['service_type']: r['count'] for r in by_type} if by_type else {},
                "last_7_days": recent['count'] if recent else 0
            }
        except Exception as e:
            log.error(f"Error obteniendo stats de códigos: {e}")
            return {"total": 0, "by_type": {}, "last_7_days": 0}
    
    def get_module_usage(self) -> List[Tuple[str, int]]:
        """
        Obtiene uso de módulos desde logs.
        
        Returns:
            Lista de tuplas (módulo, count)
        """
        try:
            usage = self.db.fetch_all(
                """
                SELECT module_name, COUNT(*) as count
                FROM system_logs
                WHERE action IS NOT NULL
                GROUP BY module_name
                ORDER BY count DESC
                LIMIT 10
                """
            )
            
            return [(r['module_name'], r['count']) for r in usage] if usage else []
        except Exception as e:
            log.error(f"Error obteniendo uso de módulos: {e}")
            return []
    
    def get_file_operations_stats(self) -> Dict:
        """
        Estadísticas de operaciones de archivos.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            # Búsquedas de archivos
            searches = self.db.fetch_one(
                """
                SELECT 
                    COUNT(*) as total_searches,
                    COALESCE(SUM(files_found), 0) as total_found
                FROM file_searches
                """
            )
            
            # Compresiones PDF
            compressions = self.db.fetch_one(
                """
                SELECT 
                    COALESCE(SUM(files_processed), 0) as total_compressed,
                    COALESCE(SUM(space_saved_mb), 0) as total_saved_mb
                FROM pdf_compressions
                """
            )
            
            return {
                "searches": searches['total_searches'] if searches else 0,
                "files_found": searches['total_found'] if searches else 0,
                "pdfs_compressed": compressions['total_compressed'] if compressions else 0,
                "space_saved_mb": float(compressions['total_saved_mb']) if compressions else 0
            }
        except Exception as e:
            log.error(f"Error obteniendo stats de archivos: {e}")
            return {
                "searches": 0,
                "files_found": 0,
                "pdfs_compressed": 0,
                "space_saved_mb": 0
            }
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene actividad reciente del sistema.
        
        Args:
            limit: Número de registros
            
        Returns:
            Lista de actividades recientes
        """
        try:
            logs = self.db.fetch_all(
                """
                SELECT module_name as module, action, message, created_at,
                       CASE WHEN level IN ('INFO', 'DEBUG') THEN 1 ELSE 0 END as success
                FROM system_logs
                WHERE action IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            
            return [dict(log_entry) for log_entry in logs] if logs else []
        except Exception as e:
            log.error(f"Error obteniendo actividad reciente: {e}")
            return []
    
    def get_summary(self) -> Dict:
        """
        Obtiene resumen completo del sistema.
        
        Returns:
            Diccionario con todas las estadísticas
        """
        return {
            "qr": self.get_qr_stats(),
            "codes": self.get_codes_stats(),
            "file_ops": self.get_file_operations_stats(),
            "module_usage": self.get_module_usage(),
            "recent_activity": self.get_recent_activity(5)
        }

