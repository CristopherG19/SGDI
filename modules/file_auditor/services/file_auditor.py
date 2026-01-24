"""
SGDI - Servicio Auditor de Archivos
====================================

Auditoría de archivos con detección de faltantes y extras.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

from core.utils.logger import get_logger, log_operation
from core.database.simple_db import get_db

log = get_logger(__name__)


class FileAuditor:
    """Auditor de archivos con detección de faltantes/extras."""
    
    def __init__(self):
        """Inicializa el auditor."""
        self.db = get_db()
    
    def parse_reference_list(self, text: str) -> Tuple[Set[str], Dict[str, Dict]]:
        """
        Procesa lista de referencia.
        
        Espera formato:
        Columna 1: OC/Orden
        Columna 2: Número de suministro
        Columnas 3+: Datos adicionales
        
        Args:
            text: Texto de la lista
            
        Returns:
            Tupla (set_numeros, dict_datos_completos)
        """
        lines = text.strip().split('\n')
        
        # Headers posibles
        headers = ["OC", "ORDEN", "N° DE SUMINISTRO", "SUMINISTRO"]
        
        # Saltar encabezados
        data_lines = lines
        if lines:
            first_line = lines[0].upper().split()
            if any(h in first_line for h in headers):
                data_lines = lines[1:]
        
        numbers = set()
        complete_data = {}
        
        for line in data_lines:
            if not line.strip():
                continue
            
            # Split por tabs o múltiples espacios
            fields = re.split(r'\t|\s{2,}', line.strip())
            
            if len(fields) >= 2:
                oc_raw = fields[0].strip()
                supply_raw = fields[1].strip()
                rest = " ".join(fields[2:]) if len(fields) > 2 else ""
                
                # Extraer solo números
                supply_num = re.sub(r'\D', '', supply_raw)
                
                if supply_num:
                    numbers.add(supply_num)
                    complete_data[supply_num] = {
                        "oc": oc_raw,
                        "supply": supply_raw,
                        "rest": rest
                    }
        
        return numbers, complete_data
    
    def scan_folder(self, 
                   folder_path: str | Path,
                   pattern: str = r'(\d+)') -> Tuple[Set[str], Dict[str, str]]:
        """
        Escanea carpeta buscando archivos.
        
        Args:
            folder_path: Carpeta a escanear
            pattern: Patrón regex para extraer ID
            
        Returns:
            Tupla (set_encontrados, dict_archivo_map)
        """
        folder_path = Path(folder_path)
        found = set()
        file_map = {}
        
        try:
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    if filename.lower().endswith('.pdf'):
                        # Extraer número del nombre
                        match = re.search(pattern, filename)
                        if match:
                            file_id = re.sub(r'\D', '', match.group(1))
                            found.add(file_id)
                            file_map[file_id] = filename
        
        except Exception as e:
            log.error(f"Error escaneando carpeta: {e}")
        
        return found, file_map
    
    def audit(self,
             folder_path: str | Path,
             reference_text: str,
             file_pattern: str = r'(\d+)') -> Dict:
        """
        Realiza auditoría completa.
        
        Args:
            folder_path: Carpeta a auditar
            reference_text: Lista de referencia
            file_pattern: Patrón para extraer IDs
            
        Returns:
            Diccionario con resultados de auditoría
        """
        log.info(f"Iniciando auditoría de: {folder_path}")
        
        # Parsear referencia
        reference_numbers, reference_data = self.parse_reference_list(reference_text)
        
        if not reference_numbers:
            log.warning("No se encontraron números en la lista de referencia")
            return {
                "reference_count": 0,
                "missing": [],
                "extra": [],
                "found_count": 0,
                "status": "error",
                "message": "Lista de referencia vacía"
            }
        
        # Escanear carpeta
        found_numbers, file_map = self.scan_folder(folder_path, file_pattern)
        
        # Comparar
        missing = reference_numbers.difference(found_numbers)
        extra = found_numbers.difference(reference_numbers)
        
        # Preparar resultados
        missing_data = []
        for num in sorted(missing):
            data = reference_data.get(num, {})
            missing_data.append({
                "number": num,
                "oc": data.get("oc", ""),
                "supply": data.get("supply", ""),
                "rest": data.get("rest", "")
            })
        
        extra_data = []
        for num in sorted(extra):
            extra_data.append({
                "number": num,
                "filename": file_map.get(num, "N/A")
            })
        
        # Estadísticas
        results = {
            "folder_path": str(folder_path),
            "reference_count": len(reference_numbers),
            "found_count": len(found_numbers),
            "missing": missing_data,
            "extra": extra_data,
            "missing_count": len(missing),
            "extra_count": len(extra),
            "status": "complete" if not missing and not extra else "discrepancies",
            "timestamp": datetime.now().isoformat()
        }
        
        # Log operación
        log_operation(
            module="file_auditor",
            action="audit",
            success=True,
            message=f"Auditoría completada: {len(missing)} faltantes, {len(extra)} extras",
            reference_count=len(reference_numbers),
            found_count=len(found_numbers),
            missing=len(missing),
            extra=len(extra)
        )
        
        # Guardar en BD
        try:
            self.db.save_file_audit(
                folder_path=str(folder_path),
                reference_count=len(reference_numbers),
                found_count=len(found_numbers),
                missing_count=len(missing),
                extra_count=len(extra),
                status=results["status"]
            )
        except Exception as e:
            log.warning(f"No se pudo guardar en BD: {e}")
        
        log.info(f"Auditoría completada: {len(missing)} faltantes, {len(extra)} extras")
        
        return results
    
    def generate_report(self, audit_results: Dict) -> str:
        """
        Genera reporte en texto plano.
        
        Args:
            audit_results: Resultados de auditoría
            
        Returns:
            Reporte en texto
        """
        lines = []
        
        # Encabezado
        lines.append("=" * 100)
        lines.append("REPORTE DE AUDITORÍA DE ARCHIVOS")
        lines.append("=" * 100)
        lines.append(f"Ruta: {audit_results['folder_path']}")
        lines.append(f"Fecha: {datetime.fromisoformat(audit_results['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Archivos esperados: {audit_results['reference_count']}")
        lines.append(f"Archivos encontrados: {audit_results['found_count']}")
        lines.append("-" * 100)
        lines.append("")
        
        # Sección faltantes
        missing = audit_results['missing']
        if missing:
            lines.append(f"SECCIÓN 1: ARCHIVOS NO ENCONTRADOS ({len(missing)})")
            lines.append("Acción requerida: Buscar estos archivos y agregarlos a la carpeta.")
            lines.append("")
            lines.append(f"{'ORDEN (OC)':<20} | {'SUMINISTRO':<15} | {'OBSERVACIÓN / DETALLE'}")
            lines.append("-" * 100)
            
            for item in missing:
                lines.append(f"{item['oc']:<20} | {item['supply']:<15} | {item['rest']}")
            
            lines.append("")
        else:
            lines.append("✓ LISTA COMPLETA: Todos los archivos de la lista están presentes.")
            lines.append("")
        
        # Sección extras
        extra = audit_results['extra']
        if extra:
            lines.append(f"SECCIÓN 2: ARCHIVOS NO LISTADOS / POSIBLE ERROR ({len(extra)})")
            lines.append("Estos archivos existen en la carpeta pero NO están en la lista.")
            lines.append("")
            lines.append(f"{'NÚMERO DETECTADO':<25} | {'NOMBRE REAL DEL ARCHIVO'}")
            lines.append("-" * 100)
            
            for item in extra:
                lines.append(f"{item['number']:<25} | {item['filename']}")
            
            lines.append("")
        else:
            if not missing:
                lines.append("✓ CARPETA LIMPIA: No hay archivos extra.")
                lines.append("")
        
        # Resumen
        if not missing and not extra:
            lines.append("=" * 100)
            lines.append("✓ AUDITORÍA PERFECTA: Todo cuadra correctamente.")
            lines.append("=" * 100)
        
        return "\n".join(lines)
