# SGDI - Sistema de Gestión Documental Integral

Un sistema unificado de gestión documental que integra 5 herramientas especializadas de procesamiento de archivos, códigos QR y PDFs.

## 🚀 Características

### Módulos Principales:

1. **📊 QR Suite**
   - Procesador de plantillas Excel con códigos QR
   - Lector y renombrador automático de archivos
   - Generador simple de códigos QR

2. **📁 Gestión de Archivos**
   - Búsqueda masiva en redes y directorios
   - Auditoría y verificación de archivos

3. **📄 Herramientas PDF**
   - Compresión inteligente de PDFs
   - Optimización de imágenes

4. **🔢 Generador de Códigos**
   - Generación de códigos únicos alfanuméricos
   - Exportación a Excel
   - Histórico persistente

5. **📊 Dashboard**
   - Métricas de operaciones
   - Estadísticas de uso
   - Accesos rápidos

## 📋 Requisitos

- Python 3.11 o superior
- Windows 10/11
- 4 GB RAM mínimo
- 500 MB espacio en disco

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/CristopherG19/SGDI.git
cd SGDI
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar environment

```bash
copy .env.example .env
# Editar .env con tus configuraciones
```

### 5. Ejecutar la aplicación

```bash
python main.py
```

## 📂 Estructura del Proyecto

```
SGDI/
├── main.py                 # Punto de entrada
├── config/                 # Configuraciones
├── core/                   # Núcleo del sistema
│   ├── database/          # Base de datos
│   └── utils/             # Utilidades compartidas
├── modules/               # Módulos funcionales
│   ├── qr_suite/
│   ├── file_management/
│   ├── pdf_tools/
│   ├── file_auditor/
│   ├── code_generator/
│   └── dashboard/
├── gui/                   # Componentes de interfaz
├── tests/                 # Tests unitarios e integración
├── docs/                  # Documentación
└── data/                  # Datos y logs
```

## 🎯 Uso Rápido

### Generar Códigos QR desde Excel

1. Abrir módulo "QR Suite" → "Procesador Excel"
2. Seleccionar archivo Excel con datos
3. Configurar columnas de datos
4. Generar y exportar PDFs

### Comprimir PDFs

1. Abrir módulo "Herramientas PDF" → "Compresión"
2. Seleccionar carpeta con PDFs
3. Ajustar calidad de compresión
4. Iniciar proceso

### Buscar Archivos en Red

1. Abrir módulo "Gestión de Archivos" → "Búsqueda Masiva"
2. Ingresar ruta de red
3. Pegar lista de archivos a buscar
4. Ejecutar búsqueda y copia

## 📖 Documentación

- **Manual de Usuario:** [docs/manual_usuario.md](docs/manual_usuario.md)
- **Documentación Técnica:** [docs/manual_tecnico.md](docs/manual_tecnico.md)

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=. --cov-report=html
```

## 🏗️ Build

```bash
# Compilar ejecutable
cd build
build.bat
```

## 🤝 Contribución

Este es un proyecto interno. Para sugerencias o reportar bugs, contactar al equipo de desarrollo.

## 📄 Licencia

Propietario - Uso interno únicamente

## 📞 Soporte

Para soporte técnico, contactar: [tu-email@ejemplo.com]

---

**Versión:** 1.0.0  
**Última actualización:** 2026-01-21
