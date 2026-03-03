# 🔐 Guía de Renovación de Credenciales de Dropbox

Este documento describe el procedimiento paso a paso para renovar y actualizar las credenciales de la API de Dropbox utilizadas por el sistema **SGDI** y la plataforma **WordPress**.

Este proceso es necesario si:
1. Las credenciales actuales se ven expuestas (ej. alerta de GitGuardian).
2. Se revoca accidentalmente el acceso de la aplicación actual en Dropbox.
3. Se requiere migrar a una nueva aplicación (App Key/Secret) por políticas de seguridad.

---

## ⚠️ Conceptos Importantes

- **App Key / App Secret**: Identifican a la aplicación. Si se filtran o se necesita rotarlos, **es obligatorio crear una nueva app en Dropbox**, ya que Dropbox no permite regenerar el *App Secret* de una app existente.
- **Refresh Token**: Es el token de acceso de larga duración. **Está ligado a un App Key/Secret específico**. Si cambias la app, el Refresh Token anterior deja de funcionar inmediatamente y debes generar uno nuevo.

---

## 🛠️ Paso 1: Crear una Nueva App en Dropbox (Si rotas el App Secret)

*Si solo necesitas generar un nuevo Refresh Token para la misma app (mismo App Key/Secret), omite este paso y ve al Paso 2.*

1. Ingresa a la [Dropbox App Console](https://www.dropbox.com/developers/apps).
2. Haz clic en **"Create app"**.
3. Configuración inicial:
   - **API**: Elige `Scoped access`.
   - **Access type**: Elige tipo de acceso (ej. `Full Dropbox`).
   - **Name**: Asigna un nuevo nombre descriptivo (ej. `SGDI-Prod-v2`).
4. En la pestaña **Settings** de tu nueva app, configura los **Redirect URIs**. Añade obligatoriamente (presionando "Add"):
   - `http://localhost:8080` (Usado por los scripts locales de Python)
   - *Cualquier otro URI que uses (ej. el callback de tu WordPress, si aplica).*
5. En la pestaña **Permissions**, marca los permisos necesarios (los mismos que tenía tu app anterior). Usualmente:
   - `files.metadata.read`
   - `files.content.read`
   - `sharing.write`
   - Haz clic en **"Submit"** al final de la página para guardar los permisos.
6. Regresa a la pestaña **Settings** y copia temporalmente en un bloc de notas el **App key** y el **App secret**.

---

## 💻 Paso 2: Actualizar `.env` y Generar Nuevo Refresh Token

Ahora debemos usar los scripts locales de SGDI para obtener el nuevo Refresh Token.

1. Abre el archivo `.env` en la raíz del proyecto SGDI.
2. Actualiza el **App Key** y **App Secret** con los valores obtenidos en el Paso 1:
   ```env
   DROPBOX_APP_KEY=tu_nuevo_app_key
   DROPBOX_APP_SECRET=tu_nuevo_app_secret
   ```
   *(Deja el `DROPBOX_REFRESH_TOKEN` viejo por ahora).*
3. Abre tu terminal en la carpeta del proyecto y navega a la carpeta de scripts de autorización:
   ```bash
   cd scripts/auth
   ```
4. Ejecuta el primer script para solicitar autorización:
   ```bash
   python paso1_autorizar_dropbox.py
   ```
   - Esto abrirá tu navegador.
   - Inicia sesión en Dropbox (si no lo has hecho) y haz clic en **"Continuar"** y luego en **"Permitir"**.
   - El script en la terminal capturará el código y se cerrará automáticamente.
5. Inmediatamente después, ejecuta el segundo script para canjear el código:
   ```bash
   python paso2_obtener_token.py
   ```
   - Este script utilizará el nuevo App Key y App Secret (que ya están en tu `.env`) para obtener un nuevo **Refresh Token**.
   - La terminal imprimirá el nuevo token y el script SQL necesario para WordPress.

---

## 🔄 Paso 3: Propagar el Nuevo Refresh Token

Debes actualizar el token recién generado en los dos sistemas que lo consumen.

### 1. En SGDI (Local)
1. Copia el nuevo token generado por el script anterior.
2. Pégalo en tu archivo `.env`:
   ```env
   DROPBOX_REFRESH_TOKEN=tu_nuevo_refresh_token
   ```
3. Guarda el archivo `.env`. Inicia SGDI y verifica en la pestaña "Dropbox" que la conexión es exitosa (`✅ Conectado`).

### 2. En WordPress (Base de Datos)
El script `paso2_obtener_token.py` generó una sentencia SQL similar a esta:
```sql
UPDATE wp_dropbox_tokens SET refresh_token = 'tu_nuevo_refresh_token' WHERE id = 1;
```
1. Accede a tu administrador de base de datos de WordPress (ej. **phpMyAdmin** en tu hosting).
2. Selecciona la base de datos de tu sitio WordPress.
3. Ve a la pestaña **SQL** (o "Consulta").
4. Pega la sentencia generada y presiona **Continuar/Ejecutar**.
5. Verifica en tu sitio web que la integración con Dropbox funcione correctamente.

---

## 🗑️ Paso 4: Limpieza de Seguridad

Si realizaste este proceso debido a una filtración de credenciales (ej. GitGuardian):

1. Vuelve a la [Dropbox App Console](https://www.dropbox.com/developers/apps).
2. Selecciona tu **aplicación anterior (la vulnerada)**.
3. Ve a la sección **"Settings"**, desplázate hasta el final y haz clic en **"Delete app"**.
   - *Al eliminar la app antigua, cualquier App Key, App Secret y Refresh Token vinculados a ella quedarán permanentemente invalidados, mitigando cualquier riesgo de seguridad.*
