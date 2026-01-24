"""
SGDI - Code Generator Module
=============================

Módulo completo para generación de códigos de seguridad INACAL.

Este paquete proporciona servicios y GUI para generar códigos de seguridad
únicos alfanuméricos para medidores de agua siguiendo el formato INACAL.
Incluye generación individual, por lotes, exportación, búsqueda y
almacenamiento histórico.

Formato INACAL:
    XXXX999999 (4 letras mayúsculas + 6 dígitos = 10 caracteres)

Submodules:
    - services.unique_code_gen: Generación de códigos únicos
    - gui.code_generator_tab: Interfaz gráfica para generación

Example:
    Uso básico del módulo::

        from modules.code_generator.services.unique_code_gen import CodeGenerator

        # Generar código único
        generator = CodeGenerator()
        success, code = generator.generate_code()
        print(f"Código: {code}")

        # Generar lote
        codes, errors = generator.generate_batch(count=100)
        print(f"Generados: {len(codes)} códigos")

Author:
    SGDI Development Team

Version:
    1.0.0
"""

__version__ = "1.0.0"
__author__ = "SGDI Development Team"

__all__ = [
    "CodeGenerator",
    "CodeGeneratorTab"
]