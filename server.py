# server.py (MODIFICADO)
from flask import Flask, request, jsonify
from datetime import datetime
import sys
import os
import requests
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

app = Flask(__name__)

# ============================================
# CONFIGURACION
# ============================================
PHONE_IP = os.getenv('PHONE_IP', 'http://192.168.1.100:8080')  # IP de tu celular
CAPTURE_VIDEO = os.getenv('CAPTURE_VIDEO', 'True').lower() == 'true'   # Si capturar video
CAPTURE_AUDIO = os.getenv('CAPTURE_AUDIO', 'True').lower() == 'true'   # Si capturar audio
DURATION = int(os.getenv('DURATION', '5'))           # Duración en segundos

alertas = []

# ============================================
# FUNCIONES DE CAPTURA
# ============================================

def capture_photo():
    """Captura foto del celular"""
    try:
        url = f"{PHONE_IP}/photo.jpg"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            os.makedirs("captures", exist_ok=True)
            filename = f"captures/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"   [FOTO] Guardada: {filename}")
            return filename
        return None
    except Exception as e:
        print(f"   [ERROR FOTO] {e}")
        return None

def record_video(duration=5):
    """
    Graba video desde el celular (stream MJPEG) durante N segundos
    y lo convierte a MP4 válido usando FFmpeg.
    """
    try:
        os.makedirs("captures", exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        raw_file = f"captures/video_{timestamp}.mjpeg"
        final_file = f"captures/video_{timestamp}.mp4"

        url = f"{PHONE_IP}/video"

        print("   [VIDEO] Grabando stream...")

        response = requests.get(url, stream=True, timeout=10)
        start_time = time.time()

        with open(raw_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                if time.time() - start_time >= duration:
                    break

        print("   [VIDEO] Stream capturado, convirtiendo a MP4...")

        # Convertir MJPEG → MP4 (reproducible)
        ffmpeg_cmd = (
            f'ffmpeg -y -loglevel error '
            f'-t {duration} '
            f'-i "{raw_file}" '
            f'-c:v libx264 -pix_fmt yuv420p "{final_file}"'
        )

        os.system(ffmpeg_cmd)

        # Borrar archivo temporal
        if os.path.exists(raw_file):
            os.remove(raw_file)

        print(f"   [VIDEO] Guardado: {final_file}")
        return final_file

    except Exception as e:
        print(f"   [ERROR VIDEO] {e}")
        return None

def record_audio(duration=5):
    """
    Graba audio desde el celular durante N segundos,
    lo guarda como WAV y lo convierte a MP3 válido.
    """
    try:
        os.makedirs("captures", exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        wav_file = f"captures/audio_{timestamp}.wav"
        mp3_file = f"captures/audio_{timestamp}.mp3"

        url = f"{PHONE_IP}/audio.wav"

        print("   [AUDIO] Grabando audio...")

        response = requests.get(url, stream=True, timeout=10)
        start_time = time.time()

        with open(wav_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)
                if time.time() - start_time >= duration:
                    break

        print("   [AUDIO] Convirtiendo a MP3...")

        ffmpeg_cmd = (
            f'ffmpeg -y -loglevel error '
            f'-t {duration} '
            f'-i "{wav_file}" '
            f'-codec:a libmp3lame -qscale:a 4 "{mp3_file}"'
        )

        os.system(ffmpeg_cmd)

        # Limpiar WAV temporal
        if os.path.exists(wav_file):
            os.remove(wav_file)

        print(f"   [AUDIO] Guardado: {mp3_file}")
        return mp3_file

    except Exception as e:
        print(f"   [ERROR AUDIO] {e}")
        return None

# ============================================
# ENDPOINTS
# ============================================

@app.route('/')
def home():
    return """
    <h1>Servidor IoT - Deteccion de Fuego</h1>
    <p>Estado: <strong style="color: green;">ACTIVO</strong></p>
    <p>Endpoints:</p>
    <ul>
        <li>POST /alert - Recibir alertas del Arduino</li>
        <li>GET /status - Estado del servidor</li>
        <li>GET /alertas - Historial de alertas</li>
    </ul>
    """

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "total_alertas": len(alertas)
    })

@app.route('/alert', methods=['POST'])
def recibir_alerta():
    """Recibe alertas del Arduino y captura multimedia si es necesario"""
    try:
        datos = request.get_json()
        
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        temperatura = datos.get('temp', 0)
        luz = datos.get('light', 0)
        estado = datos.get('status', 'unknown')
        
        alerta = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "temperatura": temperatura,
            "luz": luz,
            "estado": estado,
            "archivos": {}
        }
        
        # Mostrar en consola
        print("\n" + "="*60)
        print("[ALERTA RECIBIDA]")
        print(f"Tiempo: {alerta['timestamp']}")
        print(f"Temperatura: {temperatura} C")
        print(f"Luz: {luz}")
        print(f"Estado: {estado}")
        
        # Si es ALERTA REAL, capturar multimedia
        if estado == "alert":
            print("\n>>> DISPARANDO CAPTURA DE MULTIMEDIA <<<")
            
            # Capturar foto
            foto = capture_photo()
            if foto:
                alerta["archivos"]["photo"] = foto
            
            # Capturar video
            if CAPTURE_VIDEO:
                video = record_video(duration=DURATION)
                if video:
                    alerta["archivos"]["video"] = video
            
            # Capturar audio
            if CAPTURE_AUDIO:
                audio = record_audio(duration=DURATION)
                if audio:
                    alerta["archivos"]["audio"] = audio
            
            print(">>> CAPTURA COMPLETADA <<<")
        
        print("="*60)
        
        # Guardar en historial
        alertas.append(alerta)
        
        return jsonify({
            "status": "received",
            "message": "Alerta procesada correctamente",
            "timestamp": alerta['timestamp'],
            "archivos_capturados": list(alerta["archivos"].keys())
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error procesando alerta: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/alertas', methods=['GET'])
def ver_alertas():
    return jsonify({
        "total": len(alertas),
        "alertas": alertas[-10:]
    })

# ============================================
# MAIN
# ============================================

def obtener_ip_local():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "No se pudo obtener IP"

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SERVIDOR IoT - DETECCION DE FUEGO")
    print("="*60)
    
    ip_local = obtener_ip_local()
    puerto = int(os.getenv('PORT', 5000))  # Heroku asigna puerto dinámicamente
    
    print(f"\n[CONFIG] IP Celular: {PHONE_IP}")
    print(f"[CONFIG] Capturar video: {CAPTURE_VIDEO}")
    print(f"[CONFIG] Capturar audio: {CAPTURE_AUDIO}")
    print(f"[CONFIG] Duracion: {DURATION}s")
    
    print(f"\n[INFO] Servidor iniciando en:")
    print(f"       IP: {ip_local}")
    print(f"       Puerto: {puerto}")
    print(f"\n[INFO] Arduino debe enviar a:")
    print(f"       http://{ip_local}:{puerto}/alert")
    print("\n[INFO] Presiona Ctrl+C para detener")
    print("="*60 + "\n")
    
    # Modo debug solo en desarrollo
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=puerto, debug=debug_mode)