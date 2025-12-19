# Sistema IoT de Deteccion de Incendios con IA

Sistema de monitoreo IoT inteligente que combina sensores Arduino, captura automatica de multimedia desde dispositivos moviles y analisis con Inteligencia Artificial para detectar incendios en tiempo real.

## Equipo de Desarrollo

- **Christian Pardave Espinoza**
- **Berly Diaz Castro**
- **Diego Apaza Andaluz**
- **Merisabel Ruelas Quenaya**
- **Yanira Suni Quispe**
- **Joselyn Quispe Huanca**

## Características Principales

- **API REST** para recepción de alertas desde sensores Arduino
- **Sistema de cámara inteligente** que se activa automáticamente con alertas
- **Captura multimedia automática** (foto, video, audio) desde dispositivos móviles
- **Procesamiento con IA** mediante Google Vertex AI para detección de fuego/humo
- **Notificaciones push** en tiempo real al celular
- **Almacenamiento en la nube** con Google Cloud Storage
- **Historial de alertas** con análisis de IA incluido
- **Interfaz web moderna** para monitoreo en tiempo real
- **Integración con n8n** para envío automático de correos electrónicos

## Tecnologías Utilizadas

### Backend
- **Python Flask** - Framework web principal
- **Google Cloud Platform**:
  - App Engine (despliegue)
  - Cloud Storage (almacenamiento)
  - Vertex AI (análisis de IA)
- **Arduino** - Sensores IoT

### Frontend
- **HTML5/CSS3** - Interfaz web moderna
- **JavaScript** - Captura multimedia y notificaciones
- **MediaRecorder API** - Grabación de video/audio

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
- Dispositivo móvil con navegador moderno
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
   N8N_WEBHOOK_ALERT=https://tu-n8n-instance/webhook/send-alerta
   N8N_WEBHOOK_RESULT=https://tu-n8n-instance/webhook/send-result
   ```

5. **Ejecutar servidor local**:
   ```bash
   python server.py
   ```

   El servidor estará disponible en: `http://localhost:5000`

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
     N8N_WEBHOOK_ALERT: "https://tu-n8n-instance/webhook/send-alerta"
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

1. **Arduino detecta anomalía** → Envía alerta con temperatura/luz
2. **Sistema envía email** → Notificación para abrir cámara
3. **Usuario abre cámara** → Captura foto/video/audio automáticamente
4. **Vertex AI analiza** → Detecta presencia de fuego/humo
5. **Sistema envía resultado** → Email con confirmación o falsa alarma
6. **Dashboard actualiza** → Historial con análisis completo

## Estructura del Proyecto

```
proyecto-iot/
├── api-iot/                    # Backend Flask
│   ├── server.py              # Servidor principal
│   ├── main.py               # Punto de entrada App Engine
│   ├── requirements.txt      # Dependencias Python
│   ├── app.yaml              # Configuración App Engine
│   ├── .env                  # Variables de entorno
│   └── templates/            # Plantillas HTML
│       ├── index.html
│       ├── dashboard.html
│       └── camera.html
├── arduino/                   # Código Arduino
│   └── codigoarduino.ino
├── email-templates/          # Templates de email
│   ├── email_alerta.html
│   └── email_confirmacion.html
├── docs/                     # Documentación
│   ├── CONFIGURACION_N8N.md
│   └── INSTRUCCIONES_PARA_COMPANERO.md
└── README.md                 # Este archivo
```

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

## Pruebas

### Prueba de Alertas
```bash
# Simular alerta desde Arduino
curl -X POST https://tu-app.appspot.com/alert \
  -H "Content-Type: application/json" \
  -d '{"temp": 45.5, "light": 850, "status": "alert"}'
```

### Prueba de Webhooks
```bash
# Probar webhook de alerta
curl -X POST "https://tu-n8n-instance/webhook/send-alerta" \
  -H "Content-Type: application/json" \
  -d '{"timestamp": "2025-12-19 12:30:45", "temperature": 45.5, "light": 850}'
```

## Solución de Problemas

### Problemas Comunes

1. **Error 403 en Vertex AI**
   - Verificar permisos de service account en proyecto compañero
   - Ejecutar: `gcloud projects add-iam-policy-binding tu-vertex-project-id --member="serviceAccount:tu-proyecto-id@appspot.gserviceaccount.com" --role="roles/aiplatform.user"`

2. **Uploads no funcionan**
   - Verificar permisos de Cloud Storage
   - Revisar logs: `gcloud app logs tail -s default`

3. **Emails no llegan**
   - Verificar configuración de n8n
   - Revisar estado de workflows

## Métricas y Monitoreo

- **Dashboard en tiempo real**: `https://tu-app.appspot.com/dashboard`
- **Logs de App Engine**: `gcloud app logs tail -s default`
- **Monitoreo de bucket**: `gsutil ls gs://tu-bucket-name/**`

## Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## Contacto

- **Email**: tu-email@ejemplo.com
- **Proyecto**: Sistema IoT de Detección de Incendios
- **Institución**: Universidad Nacional de San Agustín (UNSA)

---

**¡Sistema IoT inteligente con IA listo para detectar incendios en tiempo real!**

*Desarrollado por el equipo de estudiantes de Ingeniería de Sistemas - UNSA*