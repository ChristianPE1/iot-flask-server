# Sistema IoT de Deteccion de Incendios con IA

Sistema de monitoreo IoT inteligente **completamente automático** que combina sensores Arduino, captura automática de multimedia desde IP Webcam (Android) vía ngrok, y análisis con Inteligencia Artificial para detectar incendios en tiempo real sin intervención manual.

## Características Principales

- **API REST** para recepción de alertas desde sensores Arduino
- **Captura multimedia automática** desde IP Webcam (Android) vía ngrok
- **Sistema completamente automático** - no requiere intervención manual
- **Procesamiento con IA** mediante Google Vertex AI para detección de fuego/humo
- **Captura simultánea** de foto (JPG), video (MJPEG) y audio (WAV)
- **Almacenamiento en la nube** con Google Cloud Storage
- **Análisis automático** de multimedia con IA al recibir alertas
- **Throttling inteligente** (60s cooldown) para evitar spam de capturas
- **Historial de alertas** con análisis de IA incluido
- **Interfaz web moderna** para monitoreo en tiempo real
- **Integración con n8n** para envío automático de correos electrónicos
- **Sistema de túnel seguro** con ngrok para acceso remoto

## Tecnologías Utilizadas

### Backend
- **Python Flask** - Framework web principal
- **Google Cloud Platform**:
  - App Engine (despliegue)
  - Cloud Storage (almacenamiento)
  - Vertex AI (análisis de IA)
- **Arduino** - Sensores IoT
- **ngrok** - Túnel seguro para acceso remoto a IP Webcam

### Dispositivos Móviles
- **IP Webcam (Android)** - Servidor de cámara local
- **Captura automática** desde endpoints: `/photo.jpg`, `/video`, `/audio.wav`

### Integraciones
- **n8n** - Automatización de workflows y envío de emails
- **Gmail API** - Notificaciones por correo electrónico

### Infraestructura
- **Google Cloud Storage** - Almacenamiento de archivos multimedia
- **Google Vertex AI** - Modelo de detección de fuego/humo
- **HTTPS** - Comunicación segura

## Prerrequisitos

- Python 3.11+
- Cuenta de Google Cloud Platform
- Arduino con sensores de temperatura y luz
- **Dispositivo Android con IP Webcam** (app gratuita)
- **ngrok** (para túnel seguro)
- n8n (para automatización de emails)

## Instalación Local

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd proyecto-iot/api-iot
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Crear archivo `.env`:
   ```env
   BUCKET_NAME=tu-bucket-name
   VERTEX_AI_ENDPOINT=https://REGION-aiplatform.googleapis.com/v1/projects/tu-vertex-project-id/locations/REGION/endpoints/tu-endpoint-id:predict
   ALERT_EMAIL=tu-email@ejemplo.com
   APP_URL=https://tu-app.appspot.com
   PHONE_IP=https://tu-ngrok-url.ngrok-free.dev
   N8N_WEBHOOK_RESULT=https://tu-n8n-instance/webhook/send-result
   ```

5. **Ejecutar servidor local**:
   ```bash
   python server.py
   ```

   El servidor estará disponible en: `http://localhost:5000`

## Configuración de IP Webcam y ngrok

### 1. Instalar IP Webcam (Android)
1. Descargar e instalar **IP Webcam** desde Google Play Store
2. Abrir la app y configurar:
   - Puerto: `8080` (predeterminado)
   - Activar servidor web
3. Anotar la IP local (ej: `192.168.1.100:8080`)

### 2. Instalar y configurar ngrok
1. Descargar ngrok desde https://ngrok.com
2. Crear túnel:
   ```bash
   ngrok http http://192.168.1.100:8080
   ```
3. Copiar la URL HTTPS generada (ej: `https://abc123.ngrok-free.dev`)

### 3. Verificar conexión
```bash
# Probar foto
curl -I https://tu-ngrok-url.ngrok-free.dev/photo.jpg

# Probar video
curl -I https://tu-ngrok-url.ngrok-free.dev/video

# Probar audio
curl -I https://tu-ngrok-url.ngrok-free.dev/audio.wav
```

## Despliegue en Producción

### Google App Engine

1. **Autenticarse con Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project tu-proyecto-id
   ```

2. **Configurar variables de entorno en `app.yaml`**:
   ```yaml
   env_variables:
     BUCKET_NAME: "tu-bucket-name"
     VERTEX_AI_ENDPOINT: "https://REGION-aiplatform.googleapis.com/v1/projects/tu-vertex-project-id/locations/REGION/endpoints/tu-endpoint-id:predict"
     ALERT_EMAIL: "tu-email@ejemplo.com"
     APP_URL: "https://tu-app.appspot.com"
     PHONE_IP: "https://tu-ngrok-url.ngrok-free.dev"
     N8N_WEBHOOK_RESULT: "https://tu-n8n-instance/webhook/send-result"
   ```

3. **Desplegar**:
   ```bash
   gcloud app deploy
   ```

4. **Verificar despliegue**:
   ```bash
   gcloud app browse
   ```

## Configuración del Arduino

El Arduino debe enviar datos JSON POST a:
```
https://tu-app.appspot.com/alert
```

**Formato esperado**:
```json
{
    "temp": 45.5,
    "light": 850,
    "status": "alert"
}
```

**Umbrales configurados**:
- Temperatura: > 30.0°C
- Nivel de luz: > 400
- **Throttling**: 60 segundos entre capturas automáticas

### Sistema de Throttling
- **Cooldown de 60 segundos** entre alertas automáticas
- Evita spam de emails y sobrecarga del sistema
- Solo permite una captura multimedia cada minuto

## API Endpoints

### Endpoints Principales
- `GET /` - Panel de estado del servidor
- `GET /dashboard` - Dashboard con historial de alertas y análisis
- `GET /camera` - Sistema de captura multimedia inteligente
- `POST /alert` - Recibir alertas del Arduino
- `GET /status` - Estado del servidor (JSON)
- `GET /alertas` - Historial de alertas (JSON)

### Endpoints de Upload
- `POST /upload/photo` - Recibir foto desde dispositivo móvil
- `POST /upload/video` - Recibir video desde dispositivo móvil
- `POST /upload/audio` - Recibir audio desde dispositivo móvil
- `POST /analyze` - Analizar multimedia con Vertex AI

### Endpoints de Prueba
- `POST /api/test-alert` - Simular alerta para pruebas
- `POST /send-result` - Enviar resultado de verificación manual

## Flujo de Funcionamiento

### Sistema Completamente Automático

1. **Arduino detecta anomalía** → Envía alerta con temperatura/luz (>30°C y >400 luz)
2. **Sistema recibe alerta** → Verifica throttling (60s cooldown)
3. **Captura automática inicia** → Foto (JPG), Video (5s MJPEG), Audio (5s WAV)
4. **Archivos subidos a Cloud Storage** → Google Cloud Storage bucket
5. **Vertex AI analiza automáticamente** → Detecta presencia de fuego/humo
6. **Email de resultado enviado** → Confirmación o falsa alarma vía n8n
7. **Dashboard actualiza** → Historial con análisis completo y enlaces a archivos

### Endpoints de IP Webcam utilizados:
- `https://ngrok-url.ngrok-free.dev/photo.jpg` - Captura de imagen
- `https://ngrok-url.ngrok-free.dev/video` - Stream de video MJPEG
- `https://ngrok-url.ngrok-free.dev/audio.wav` - Stream de audio WAV

### Protección contra spam:
- **Throttling de 60 segundos** entre capturas automáticas
- Evita múltiples emails y sobrecarga del sistema


## Almacenamiento en la Nube

### Google Cloud Storage
- **Bucket**: `tu-bucket-name`
- **Estructura**:
  ```
  gs://tu-bucket-name/
  ├── photos/     # Fotos JPG
  ├── videos/     # Videos WebM
  └── audio/      # Audio WebM
  ```

### URLs Públicas
Los archivos son accesibles públicamente:
```
https://storage.googleapis.com/tu-bucket-name/photos/
https://storage.googleapis.com/tu-bucket-name/videos/
https://storage.googleapis.com/tu-bucket-name/audio/
```

## Modelo de IA (Vertex AI)
- **Github**: https://github.com/Berly01/Yolo-Fire-Smoke-Detector.git
- **Proyecto**: `tu-vertex-project-id`
- **Endpoint**: Detección de fuego/humo con YOLO v11
- **Confianza**: Análisis de imágenes y videos
- **Características**:
  - Detección de fuego en tiempo real
  - Análisis de audio para sonidos característicos
  - Frame-by-frame analysis para videos

## Sistema de Notificaciones

### n8n Workflows
- **Webhook `/send-alerta`**: Email cuando se detecta posible incendio
- **Webhook `/send-result`**: Email con resultado del análisis de IA

### Gmail Integration
- Emails automáticos con templates HTML profesionales
- Notificaciones en tiempo real
- Links directos a dashboard y cámara

#### Dashboard Web
![Web_Dashboard](https://github.com/user-attachments/assets/4beb030f-5b92-4491-b888-c1adb58c9323)

#### Confirmación de Incendio enviado via Gmail
![Web_Confirmacion_Alerta](https://github.com/user-attachments/assets/a666ecad-3e29-4983-8692-9c32c9e062d4)


## Pruebas

### Prueba de Conexión ngrok
```bash
# Verificar que ngrok esté funcionando
curl -I https://tu-ngrok-url.ngrok-free.dev/photo.jpg

# Probar captura automática
curl -X POST https://tu-app.appspot.com/api/test-alert
```

### Prueba de Alertas
```bash
# Simular alerta desde Arduino
curl -X POST https://tu-app.appspot.com/alert \
  -H "Content-Type: application/json" \
  -d '{"temp": 45.5, "light": 850, "status": "alert"}'
```

### Verificación de Archivos
```bash
# Ver fotos capturadas
gcloud storage ls gs://tu-bucket-name/photos/

# Ver videos capturados
gcloud storage ls gs://tu-bucket-name/videos/

# Ver audio capturado
gcloud storage ls gs://tu-bucket-name/audio/
```


## Métricas y Monitoreo

- **Dashboard en tiempo real**: `https://tu-app.appspot.com/dashboard`
- **Logs de App Engine**: `gcloud app logs tail -s default`
- **Monitoreo de bucket**: `gsutil ls gs://tu-bucket-name/**`

### Troubleshooting

#### Problemas con ngrok
```bash
# Verificar si ngrok está corriendo
ps aux | grep ngrok

# Reiniciar túnel ngrok
./start-ngrok.sh

# Verificar conectividad
curl -I https://tu-ngrok-url.ngrok-free.dev/photo.jpg
```

#### Problemas de captura
```bash
# Ver logs de captura
gcloud app logs tail -s default | grep "PHOTO\|VIDEO\|AUDIO"

# Probar endpoint manualmente
curl -X POST https://tu-app.appspot.com/api/test-alert
```

#### URL de ngrok expirada
1. Reiniciar ngrok: `./start-ngrok.sh`
2. Obtener nueva URL
3. Actualizar `app.yaml` con nueva URL
4. Re-desplegar: `gcloud app deploy --quiet`

## URL de ngrok

**La URL de ngrok cambia cada vez que se reinicia el túnel.** Si ngrok se detiene o reinicia:

1. **Ejecutar**: `./start-ngrok.sh`
2. **Copiar nueva URL** (ej: `https://nueva-url.ngrok-free.dev`)
3. **Actualizar `app.yaml`**:
   ```yaml
   PHONE_IP: "https://nueva-url.ngrok-free.dev"
   ```
4. **Re-desplegar**: `gcloud app deploy --quiet`

**Sin esto, el sistema no podrá capturar multimedia automáticamente.**


## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE.md` para más detalles.
