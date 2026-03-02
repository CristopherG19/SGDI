# SGDI - Sistema de Gestión Documental Integral

Un sistema unificado de gestión documental que integra 7 herramientas especializadas de procesamiento de archivos, códigos QR, PDFs, e integraciones en la nube.

## 🚀 Características

### Módulos Principales:

1. **📊 Dashboard**
   - Panel de control con métricas de operaciones
   - Estadísticas de uso del sistema
   - Accesos rápidos a los módulos más frecuentados

2. **📱 QR Suite**
   - **Procesador Excel:** Permite automatizar la creación de códigos QR a partir de plantillas
   - **Lector QR:** Lee e identifica códigos QR de imágenes, con capacidades de renombrado automático
   - **Generador QR:** Crea y renderiza códigos unitarios de forma ágil

3. **📁 Buscador de Archivos**
   - Búsqueda masiva y avanzada en directorios y rutas de red
   - Funciones estructuradas para copiar, clasificar y reubicar archivos

4. **📄 Compresor PDF**
   - Herramienta específica para reducción de peso de documentos PDF
   - Compresión inteligente y optimización

5. **🔍 Auditor de Archivos**
   - Verificación integral, auditorías de integridad y recolección de metadatos de archivos

6. **🔢 Generador de Códigos (INACAL)**
   - Creación de códigos alfanuméricos únicos y especializados
   - Soporte de exportación de rangos estructurados a Excel y persistencia de historial

7. **☁️ Extractor Dropbox**
   - Módulo para integración directa con Dropbox
   - Descarga y extracción automatizada de archivos de cuentas de nube

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
# Editar .env con tus credenciales y configuración (Tokens de Dropbox, etc.)
```

### 5. Ejecutar la aplicación

```bash
python main.py
```

## 📂 Estructura del Proyecto

```
SGDI/
├── main.py                 # Punto de entrada de la aplicación
├── config/                 # Configuraciones
├── core/                   # Núcleo del sistema (base de datos, utils globales)
├── gui/                    # Componentes base y ventana principal UI
├── modules/                # Módulos funcionales y herramientas:
│   ├── dashboard/ 
│   ├── qr_suite/
│   ├── file_management/
│   ├── pdf_tools/
│   ├── file_auditor/
│   ├── code_generator/
│   └── dropbox_extractor/
├── scripts/                # Scripts de apoyo (ej. construccion del build)
├── tests/                  # Pruebas integradas
├── assets/                 # Recursos y logos de la aplicación
└── data/                   # Datos locales y logs
```

## 🎯 Uso Rápido

### Procesar Excel para códigos QR
1. Abrir módulo **"QR Suite"** → **"Procesador Excel"**
2. Cargar el documento Excel fuente
3. Seleccionar las columnas necesarias de datos
4. Ejecutar la generación masiva y exportación a PDF

### Integración con Dropbox
1. Abrir módulo **"Extractor Dropbox"**
2. Asegurar que las credenciales están configuradas en el archivo `.env`
3. Seleccionar las carpetas a sincronizar o extraer y procesar localmente

### Comprimir y Auditar Archivos
- **Compresión PDF**: Usar "Compresor PDF", seleccionar carpeta principal, regular nivel de compresión y arrancar el motor.
- **Auditoría**: Usar "Auditor Archivos" tras procesamientos masivos para verificar la integridad del trabajo resultante.

## 🧪 Testing

```bash
# Ejecutar todos los tests del sistema
pytest

# Con reporte del coverage
pytest --cov=. --cov-report=html
```

## 🏗️ Build

Para compilar el sistema en un ejecutable cerrado para Windows:

```bash
cd scripts
# Ejecutar el script que utilice de build (por ejemplo `build.bat` si existe, o usar PyInstaller)
```

## 🤝 Contribución

Este es un proyecto interno. Para sugerencias o reportar bugs, contactar al equipo de desarrollo (Cristopher).

## 📄 Licencia

Propietario - Uso interno únicamente.

## 📞 Soporte

Para soporte técnico de la herramienta comunicarse con el administrador del repositorio.

---

**Versión:** 1.0.0  
**Última actualización:** 2026-03-02
