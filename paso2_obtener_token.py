"""
Script para obtener el Refresh Token desde el código de autorización
====================================================================
"""

import requests
import os

# Credenciales
APP_KEY = "woij6xbs2b72ecq"
APP_SECRET = "u16yw43f21nazoo"

print("=" * 60)
print("PASO 2: Obtener Refresh Token")
print("=" * 60)

# Intentar leer el código del archivo temporal
code = None
if os.path.exists("temp_code.txt"):
    with open("temp_code.txt", "r") as f:
        code = f.read().strip()
    print(f"\n✅ Código cargado desde temp_code.txt")
else:
    print("\nPega el código de autorización:")
    code = input("> ").strip()

print(f"\n🔄 Intercambiando código por refresh token...")

# Intercambiar código por tokens
data = {
    'code': code,
    'grant_type': 'authorization_code',
    'client_id': APP_KEY,
    'client_secret': APP_SECRET,
    'redirect_uri': 'http://localhost:8080'  # DEBE coincidir con paso 1
}

try:
    response = requests.post(
        'https://api.dropboxapi.com/oauth2/token',
        data=data
    )
    response.raise_for_status()
    
    tokens = response.json()
    
    print("\n" + "=" * 60)
    print("✅ ¡ÉXITO! Tokens obtenidos:")
    print("=" * 60)
    
    refresh_token = tokens.get('refresh_token')
    access_token = tokens.get('access_token')
    
    print(f"\n🔑 REFRESH TOKEN (el que necesitas):")
    print(f"{refresh_token}")
    
    print(f"\n\n📋 COPIA Y PEGA EN TU .env:")
    print(f"DROPBOX_REFRESH_TOKEN={refresh_token}")
    
    print(f"\n\n💾 TAMBIÉN actualiza en tu BD de WordPress:")
    print(f"UPDATE wp_dropbox_tokens SET refresh_token = '{refresh_token}' WHERE id = 1;")
    
    # Guardar en archivo
    with open("nuevo_refresh_token.txt", "w") as f:
        f.write(f"DROPBOX_REFRESH_TOKEN={refresh_token}\n")
        f.write(f"\nSQL para WordPress:\n")
        f.write(f"UPDATE wp_dropbox_tokens SET refresh_token = '{refresh_token}' WHERE id = 1;\n")
    
    print("\n✅ Token guardado en: nuevo_refresh_token.txt")
    
    # Limpiar archivo temporal
    if os.path.exists("temp_code.txt"):
        os.remove("temp_code.txt")
    
except requests.exceptions.HTTPError as e:
    print(f"\n❌ Error al obtener tokens: {e}")
    print(f"Respuesta: {e.response.text}")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")
