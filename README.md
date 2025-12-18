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

## 🌐 Despliegue en Heroku

### Prerrequisitos
- Cuenta de Heroku vinculada a `christianyunho@gmail.com`
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalado
- Git inicializado

### Pasos de despliegue

1. **Inicializar Git** (si no existe):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Crear app en Heroku**:
   ```bash
   heroku login
   heroku create tu-app-iot-fuego
   ```

3. **Configurar variables de entorno en Heroku**:
   ```bash
   heroku config:set PHONE_IP=http://TU_IP_CELULAR:8080
   heroku config:set CAPTURE_VIDEO=True
   heroku config:set CAPTURE_AUDIO=True
   heroku config:set DURATION=5
   ```

4. **Agregar buildpack de FFmpeg**:
   ```bash
   heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg
   heroku buildpacks:add --index 2 heroku/python
   ```

5. **Desplegar**:
   ```bash
   git push heroku main
   ```

## 📱 Configuración del Arduino

Tu Arduino debe enviar datos JSON a:
```
https://tu-app-iot-fuego.herokuapp.com/alert
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
├── server.py           # Servidor Flask principal
├── requirements.txt    # Dependencias Python
├── Procfile           # Configuración Heroku
├── runtime.txt        # Versión Python
├── .env              # Variables locales
├── .gitignore        # Archivos ignorados
└── README.md         # Este archivo
```

## 🎥 Funcionalidades Multimedia

- **Fotos**: Captura automática desde `/photo.jpg`
- **Videos**: Stream MJPEG convertido a MP4
- **Audio**: Grabación WAV convertida a MP3
- **Almacenamiento**: Carpeta `captures/` (ignorada en Git)

## 🔧 Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `PHONE_IP` | IP del celular con cámara | `http://192.168.1.100:8080` |
| `CAPTURE_VIDEO` | Habilitar captura de video | `True` |
| `CAPTURE_AUDIO` | Habilitar captura de audio | `True` |
| `DURATION` | Duración de grabaciones (seg) | `5` |
| `PORT` | Puerto del servidor | `5000` |
| `FLASK_ENV` | Entorno Flask | `production` |

## 📞 Soporte

Para problemas o mejoras, contactar a: **christianyunho@gmail.com**

---
*Proyecto IoT - Sistema de Detección de Incendios 🔥*