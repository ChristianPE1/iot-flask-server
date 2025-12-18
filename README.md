# 🔥 Servidor IoT - Detección de Fuego

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

### ☁️ **Estructura en Cloud Storage**
```
gs://iot-captures-481620/
├── photos/           # Fotos capturadas
├── videos/           # Videos convertidos a MP4
└── audio/            # Audio convertido a MP3
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

## 📞 Soporte

Para problemas o mejoras, contactar a: **christianyunho@gmail.com**

---
*Proyecto IoT - Sistema de Detección de Incendios 🔥*