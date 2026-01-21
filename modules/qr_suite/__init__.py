"""
SGDI - QR Suite Module
=======================

M\u00f3dulo completo para generaci\u00f3n, lectura y procesamiento de c\u00f3digos QR.

Este paquete proporciona servicios y GUI para trabajar con c\u00f3digos QR, incluyendo:
- Generaci\u00f3n de QRs individuales y por lotes
- Lectura de QRs desde PDFs e im\u00e1genes
- Renombrado autom\u00e1tico de archivos basado en QR
- Interfaces gr\u00e1ficas interactivas

Submodules:
    - services.qr_generator: Generaci\u00f3n de c\u00f3digos QR
    - services.qr_reader: Lectura y procesamiento de QR
    - gui.generador_qr_tab: Interfaz para generaci\u00f3n
    - gui.lector_qr_tab: Interfaz para lectura

Example:
    Uso b\u00e1sico del m\u00f3dulo::

        from modules.qr_suite.services.qr_generator import QRGenerator
        from modules.qr_suite.services.qr_reader import QRReader

        # Generar QR
        gen = QRGenerator()
        success, path = gen.generate_single(\"Hola\", \"qr.png\")

        # Leer QR
        reader = QRReader()
        success, content, msg = reader.read_from_image(\"qr.png\")

Author:
    SGDI Development Team

Version:
    1.0.0
"""

__version__ = "1.0.0"
__author__ = "SGDI Development Team"

__all__ = [
    "QRGenerator",
    "QRReader",
    "GeneradorQRTab",
    "LectorQRTab"
]