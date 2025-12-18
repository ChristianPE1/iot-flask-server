# 🔥## 🚀 **Caracter## 📡 **Endpoints**

- `GET /` - Panel de estado del servidor
- `GET /camera` - **Sistema de cámara inteligente** 📱
- `POST /alert` - Recibir alertas del Arduino
- `GET /status` - Estado del servidor (JSON)
- `GET /alertas` - Historial de alertas con análisis de IA (JSON)
- `POST /upload/photo` - Recibir foto desde celular
- `POST /upload/video` - Recibir video desde celular
- `POST /upload/audio` - Recibir audio desde celulars**

- **API REST** para recibir alertas de sensores Arduino
- **Sistema de cámara inteligente** que se activa automáticamente con alertas
- **Procesamiento multimedia** con FFmpeg y almacenamiento en la nube
- **Análisis con IA** mediante Vertex AI para detección de fuego/humo
- **Notificaciones push** al celular en tiempo real
- **Historial de alertas** con análisis de IA incluido
- **Interfaz web** moderna para monitoreo en tiempo realor IoT - Detección de Fuego

Sistema de monitoreo IoT que recibe alertas de sensores Arduino y captura multimedia automáticamente desde dispositivos móviles cuando se detecta una emergencia.

## 🚀 Características

- **API REST** para recibir alertas de sensores Arduino
- **Captura automática** de fotos, videos y audio desde celular
- **Procesamiento multimedia** con FFmpeg
- **Historial de alertas** con timestamps
- **Interfaz web** simple para monitoreo

## 📡 Endpoints

- `GET /` - Panel de estado del servidor
- `POST /alert` - Recibir alertas del Arduino
- `GET /status` - Estado del servidor (JSON)
- `GET /alertas` - Historial de alertas (JSON)

## 🛠️ Instalación Local

1. **Clonar repositorio**:
   ```bash
   git clone <tu-repo>
   cd api-iot
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:
   Copia `.env` y ajusta la IP de tu celular:
   ```bash
   PHONE_IP=http://TU_IP_CELULAR:8080
   CAPTURE_VIDEO=True
   CAPTURE_AUDIO=True
   DURATION=5
   ```

4. **Ejecutar servidor**:
   ```bash
   python server.py
   ```

## 🌐 Despliegue en Google App Engine

### Prerrequisitos
- Cuenta de Google Cloud vinculada a `christianyunho@gmail.com`
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) instalado
- Proyecto `project-iot` creado en Google Cloud Console

### Pasos de despliegue

1. **Autenticarse con la cuenta correcta**:
   ```bash
   gcloud auth login christianyunho@gmail.com
   gcloud config set project project-iot
   ```

2. **Verificar configuración**:
   ```bash
   gcloud config list
   ```

3. **Configurar variables de entorno en app.yaml**:
   Edita `app.yaml` y cambia `PHONE_IP` por tu IP real del celular.

4. **Desplegar en App Engine**:
   ```bash
   gcloud app deploy
   ```

5. **Abrir la aplicación**:
   ```bash
   gcloud app browse
   ```

## 📱 Configuración del Arduino

Tu Arduino debe enviar datos JSON a:
```
https://project-iot-481620.ue.r.appspot.com/alert
```

Formato esperado:
```json
{
    "temp": 85.5,
    "light": 800,
    "status": "alert"
}
```

## 📂 Estructura del Proyecto

```
api-iot/
├── server.py           # Servidor Flask principal (con Cloud Storage)
├── main.py            # Punto de entrada App Engine
├── requirements.txt    # Dependencias Python
├── app.yaml           # Configuración App Engine
├── .env              # Variables locales
├── .gitignore        # Archivos ignorados
└── README.md         # Este archivo
```

### ☁️ **Acceso a Archivos en Cloud Storage**

Los archivos capturados están disponibles públicamente en:
```
https://storage.googleapis.com/iot-captures-481620/
```

Ejemplos de URLs:
- Fotos: `https://storage.googleapis.com/iot-captures-481620/photos/photo_20251218_170000.jpg`
- Videos: `https://storage.googleapis.com/iot-captures-481620/videos/video_20251218_170000.mp4`
- Audio: `https://storage.googleapis.com/iot-captures-481620/audio/audio_20251218_170000.mp3`

### 📊 **Monitoreo del Bucket**

Para ver los archivos almacenados:
```bash
gsutil ls gs://iot-captures-481620/**
```

## ☁️ **Almacenamiento en la Nube**

- **Google Cloud Storage**: Todas las capturas (fotos, videos, audio) se almacenan automáticamente en Cloud Storage
- **URLs públicas**: Los archivos son accesibles públicamente para visualización inmediata
- **Organización**: Archivos organizados en carpetas `photos/`, `videos/`, `audio/`
- **Persistencia**: Los archivos permanecen disponibles incluso si el contenedor se reinicia

## 🔧 Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `PHONE_IP` | IP del celular con cámara | `http://192.168.1.100:8080` |
| `CAPTURE_VIDEO` | Habilitar captura de video | `True` |
| `CAPTURE_AUDIO` | Habilitar captura de audio | `True` |
| `DURATION` | Duración de grabaciones (seg) | `5` |
| `BUCKET_NAME` | Nombre del bucket de Cloud Storage | `iot-captures-481620` |
| `PORT` | Puerto del servidor | `5000` |
| `FLASK_ENV` | Entorno Flask | `production` |

## � **Cómo usar el sistema:**

1. **Configura tu Arduino** con el código actualizado (usa HTTPS y puerto 443)
2. **Abre el sistema de cámara** en tu celular: `https://project-iot-481620.ue.r.appspot.com/camera`
3. **Dale permisos** de cámara, micrófono y notificaciones
4. **¡El sistema funcionará automáticamente!** 
   - Arduino detecta calor/luz → Envía alerta → Celular captura evidencia → IA analiza contenido

## 📱 **Sistema de Cámara Inteligente:**
- Se activa **solo cuando hay alertas** de fuego
- Captura **foto + video + audio** automáticamente
- **Notificaciones push** en tiempo real
- **Análisis con IA** para verificar presencia de fuego/humo

## �📞 Soporte

Para problemas o mejoras, contactar a: **christianyunho@gmail.com**

---
**¡Tu sistema IoT inteligente con IA está listo para detectar incendios en tiempo real!** 🔥🚨🤖