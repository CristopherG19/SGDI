"""
SGDI - Export Service
=====================

Servicio para exportar URLs extraídas a diferentes formatos.
"""

import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from core.utils.logger import get_logger

log = get_logger(__name__)


class ExportService:
    """Servicio para exportar resultados de extracción."""
    
    def __init__(self):
        """Inicializa el servicio de exportación."""
        self.templates = {
            'standard': self._template_standard,
            'detailed': self._template_detailed,
            'simple': self._template_simple
        }
    
    def export_to_excel(
        self,
        data: List[Dict],
        output_path: str,
        template: str = 'standard'
    ) -> bool:
        """
        Exporta datos a Excel con formato específico.
        
        Args:
            data: Lista de diccionarios con información de archivos
            output_path: Ruta del archivo de salida
            template: Nombre de la plantilla a usar
            
        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            # Aplicar plantilla
            df = self.apply_template(data, template)
            
            if df.empty:
                log.warning("No hay datos para exportar")
                return False
            
            # Asegurar que el directorio existe
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Exportar a Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='URLs', index=False)
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets['URLs']
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    # Limitar ancho máximo
                    max_length = min(max_length, 100)
                    worksheet.column_dimensions[chr(64 + idx)].width = max_length + 2
            
            log.info(f"Exportación exitosa a {output_path}")
            return True
            
        except Exception as e:
            log.error(f"Error al exportar a Excel: {e}")
            return False
    
    def export_to_csv(
        self,
        data: List[Dict],
        output_path: str,
        template: str = 'standard'
    ) -> bool:
        """
        Exporta datos a CSV.
        
        Args:
            data: Lista de diccionarios con información de archivos
            output_path: Ruta del archivo de salida
            template: Nombre de la plantilla a usar
            
        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            # Aplicar plantilla
            df = self.apply_template(data, template)
            
            if df.empty:
                log.warning("No hay datos para exportar")
                return False
            
            # Asegurar que el directorio existe
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Exportar a CSV
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            log.info(f"Exportación exitosa a {output_path}")
            return True
            
        except Exception as e:
            log.error(f"Error al exportar a CSV: {e}")
            return False
    
    def apply_template(self, data: List[Dict], template_name: str) -> pd.DataFrame:
        """
        Aplica una plantilla a los datos.
        
        Args:
            data: Lista de diccionarios con información
            template_name: Nombre de la plantilla
            
        Returns:
            DataFrame con datos formateados
        """
        if not data:
            return pd.DataFrame()
        
        # Obtener función de plantilla
        template_func = self.templates.get(template_name, self._template_standard)
        
        # Aplicar plantilla
        return template_func(data)
    
    def _template_standard(self, data: List[Dict]) -> pd.DataFrame:
        """
        Plantilla estándar con información completa.
        
        Args:
            data: Lista de diccionarios
            
        Returns:
            DataFrame formateado
        """
        df = pd.DataFrame(data)
        
        # Seleccionar y ordenar columnas
        columns = [
            ('name', 'Nombre Archivo'),
            ('parent_folder', 'Carpeta'),
            ('folder_type', 'Tipo Verificación'),
            ('url', 'URL Compartida'),
            ('size', 'Tamaño (bytes)'),
            ('modified', 'Fecha Modificación'),
            ('extraction_date', 'Fecha Extracción')
        ]
        
        result_columns = {}
        for col, label in columns:
            if col in df.columns:
                result_columns[col] = label
        
        df = df[[col for col, _ in columns if col in df.columns]]
        df.rename(columns=result_columns, inplace=True)
        
        # Formatear tamaño
        if 'Tamaño (bytes)' in df.columns:
            df['Tamaño'] = df['Tamaño (bytes)'].apply(self._format_file_size)
            df.drop(columns=['Tamaño (bytes)'], inplace=True)
        
        # Formatear fechas
        for date_col in ['Fecha Modificación', 'Fecha Extracción']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return df
    
    def _template_detailed(self, data: List[Dict]) -> pd.DataFrame:
        """
        Plantilla detallada con toda la información disponible.
        
        Args:
            data: Lista de diccionarios
            
        Returns:
            DataFrame formateado
        """
        df = pd.DataFrame(data)
        
        # Renombrar columnas
        rename_map = {
            'name': 'Nombre',
            'path': 'Ruta Completa',
            'parent_folder': 'Carpeta Padre',
            'folder_type': 'Tipo Verificación',
            'url': 'URL Compartida',
            'size': 'Tamaño (bytes)',
            'modified': 'Fecha Modificación',
            'extraction_date': 'Fecha Extracción',
            'id': 'ID Dropbox'
        }
        
        df.rename(columns=rename_map, inplace=True)
        
        # Formatear tamaño
        if 'Tamaño (bytes)' in df.columns:
            df['Tamaño Legible'] = df['Tamaño (bytes)'].apply(self._format_file_size)
        
        return df
    
    def _template_simple(self, data: List[Dict]) -> pd.DataFrame:
        """
        Plantilla simple con información básica.
        
        Args:
            data: Lista de diccionarios
            
        Returns:
            DataFrame formateado
        """
        df = pd.DataFrame(data)
        
        # Solo columnas esenciales
        columns = ['name', 'url', 'folder_type']
        df = df[[col for col in columns if col in df.columns]]
        
        df.rename(columns={
            'name': 'Archivo',
            'url': 'URL',
            'folder_type': 'Tipo'
        }, inplace=True)
        
        return df
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """
        Formatea el tamaño de archivo a formato legible.
        
        Args:
            size_bytes: Tamaño en bytes
            
        Returns:
            String formateado (ej: "1.5 MB")
        """
        if pd.isna(size_bytes) or size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_idx = 0
        
        while size >= 1024 and unit_idx < len(units) - 1:
            size /= 1024
            unit_idx += 1
        
        return f"{size:.2f} {units[unit_idx]}"
    
    def get_available_templates(self) -> List[str]:
        """
        Retorna la lista de plantillas disponibles.
        
        Returns:
            Lista de nombres de plantillas
        """
        return list(self.templates.keys())
