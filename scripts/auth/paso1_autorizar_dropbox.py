"""
Script MEJORADO para generar Refresh Token de Dropbox
=====================================================

Este script crea un servidor temporal que captura automáticamente el código.
"""

import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Credenciales
APP_KEY = "woij6xbs2b72ecq"

# Variable global para almacenar el código
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    """Handler que captura el código de OAuth"""
    
    def do_GET(self):
        global auth_code
        
        # Parsear la URL para obtener el código
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            
            # Respuesta HTML de éxito
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Autorización Exitosa</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✅ ¡Autorización Exitosa!</h1>
                <p>Ya puedes cerrar esta ventana y volver a la terminal.</p>
                <p>El código se capturó correctamente.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Error: No se recibio el codigo")
    
    def log_message(self, format, *args):
        # Silenciar logs del servidor
        pass

print("=" * 60)
print("GENERADOR DE REFRESH TOKEN - DROPBOX")
print("=" * 60)

# Iniciar servidor HTTP en puerto 8080
port = 8080
server = HTTPServer(('localhost', port), CallbackHandler)

print(f"\n✅ Servidor temporal iniciado en http://localhost:{port}")

# Construir URL de autorización con el puerto correcto
params = {
    'client_id': APP_KEY,
    'response_type': 'code',
    'token_access_type': 'offline',
    'redirect_uri': f'http://localhost:{port}'
}

auth_url = f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"

print("\n📋 Instrucciones:")
print("1. Se abrirá tu navegador")
print("2. Click en 'Continuar' y luego 'Permitir'")
print("3. Serás redirigido automáticamente")
print("4. ¡El código se capturará solo!")

print("\nPresiona ENTER para continuar...")
input()

# Abrir navegador
webbrowser.open(auth_url)

print("\n⏳ Esperando autorización...")
print("(El servidor se detendrá automáticamente después de recibir el código)\n")

# Esperar una sola petición
server.handle_request()

if auth_code:
    print("\n" + "=" * 60)
    print("✅ ¡CÓDIGO CAPTURADO!")
    print("=" * 60)
    
    # Guardar código
    with open("temp_code.txt", "w") as f:
        f.write(auth_code)
    
    print(f"\n🔑 Código: {auth_code[:30]}...")
    print(f"\n✅ Guardado en: temp_code.txt")
    print(f"\nAhora ejecuta: python paso2_obtener_token.py")
else:
    print("\n❌ No se pudo capturar el código")
    print("Intenta de nuevo o verifica la configuración de la app")
