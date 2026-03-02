"""
Test DIRECTO de extracción de URLs - Sin GUI
Esto verifica que el código funciona correctamente
"""
import os
from dotenv import load_dotenv

load_dotenv()

from modules.dropbox_extractor.services.dropbox_client import DropboxClient
from modules.dropbox_extractor.services.url_extractor import URLExtractor

# Cargar credenciales
refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
app_key = os.getenv('DROPBOX_APP_KEY')
app_secret = os.getenv('DROPBOX_APP_SECRET')

print("=" * 60)
print("TEST DIRECTO DE EXTRACCIÓN DE URLs")
print("=" * 60)

# 1. Crear cliente y conectar
print("\n1. Conectando a Dropbox...")
client = DropboxClient(refresh_token, app_key, app_secret)
if not client.connect():
    print("❌ Error de conexión")
    exit(1)
print("✅ Conectado")

# 2. Crear extractor
print("\n2. Creando extractor...")
extractor = URLExtractor(client)

# 3. Configuración
config = {
    'root_path': '/INACAL',
    'folder_types': ['INICIAL'],
    'folder_pattern': '20251127',
    'date_from': None,
    'date_to': None,
    'rate_limit_pause': 0.1
}

print(f"\n3. Configuración:")
print(f"   - root_path: {config['root_path']}")
print(f"   - folder_pattern: {config['folder_pattern']}")
print(f"   - folder_types: {config['folder_types']}")

# 4. Callback simple
def simple_progress(current, total, info):
    status = info.get('status', 'unknown')
    print(f"   Progreso: {current}/{total} - Estado: {status}")

# 5. Ejecutar extracción
print("\n4. Iniciando extracción...")
try:
    results = extractor.extract_urls(config, progress_callback=simple_progress, url_cache={})
    
    print(f"\n5. ✅ Extracción completada!")
    print(f"   URLs extraídas: {len(results)}")
    
    if results:
        print("\n   Primeras 5 URLs:")
        for i, r in enumerate(results[:5]):
            print(f"   {i+1}. {r.get('name', 'N/A')}")
            print(f"      URL: {r.get('url', 'N/A')[:60]}...")
    
    # Estadísticas
    stats = extractor.get_extraction_stats()
    print(f"\n   Estadísticas:")
    print(f"   - Total encontrados: {stats['total_found']}")
    print(f"   - URLs extraídas: {stats['urls_extracted']}")
    print(f"   - Desde cache: {stats['cached']}")
    print(f"   - Errores: {stats['errors']}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
