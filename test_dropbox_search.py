"""
Script de diagnóstico para probar la búsqueda de carpetas en Dropbox
"""
import os
from dotenv import load_dotenv

load_dotenv()

from modules.dropbox_extractor.services.dropbox_client import DropboxClient

# Cargar credenciales
refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
app_key = os.getenv('DROPBOX_APP_KEY')
app_secret = os.getenv('DROPBOX_APP_SECRET')

print("=" * 60)
print("TEST DE BÚSQUEDA DE CARPETAS EN DROPBOX")
print("=" * 60)

# Crear cliente
client = DropboxClient(refresh_token, app_key, app_secret)

# Conectar
print("\n1. Conectando a Dropbox...")
if client.connect():
    print("✅ Conexión exitosa")
else:
    print("❌ Error de conexión")
    exit(1)

# Probar find_folders
print("\n2. Probando find_folders('20251127', '/INACAL')...")
folders = client.find_folders('20251127', '/INACAL')

if folders:
    print(f"✅ Encontradas {len(folders)} carpetas:")
    for f in folders:
        print(f"   - {f['path']}")
else:
    print("❌ No se encontraron carpetas")
    
    # Diagnóstico adicional
    print("\n3. Listando carpetas en /INACAL/VERIFICACION INICIAL...")
    try:
        result = client.dbx.files_list_folder('/INACAL/VERIFICACION INICIAL')
        print(f"   Encontradas {len(result.entries)} entradas")
        # Mostrar primeras 10
        for i, entry in enumerate(result.entries[:10]):
            print(f"   - {entry.name}")
        if len(result.entries) > 10:
            print(f"   ... y {len(result.entries) - 10} más")
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "=" * 60)
print("FIN DEL TEST")
print("=" * 60)
