# server.py (MODIFICADO)
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import sys
import os
import requests
import time
import json
from dotenv import load_dotenv
from google.cloud import storage
from google.auth import default
from google.auth.transport.requests import Request

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

# Configuración Cloud Storage
BUCKET_NAME = os.getenv('BUCKET_NAME', 'iot-captures-481620')
storage_client = storage.Client()

# Configuración Vertex AI
VERTEX_AI_ENDPOINT = os.getenv('VERTEX_AI_ENDPOINT', 'https://southamerica-east1-aiplatform.googleapis.com/v1/projects/peaceful-impact-478922-t6/locations/southamerica-east1/endpoints/4530889505971896320:predict')
VERTEX_AI_PROJECT = os.getenv('VERTEX_AI_PROJECT', 'peaceful-impact-478922-t6')

# Cliente de autenticación
try:
    # Intentar usar credenciales por defecto (funciona en App Engine)
    credentials, project = default()
    print(f"   [AUTH] Usando credenciales por defecto, proyecto: {project}")
except Exception as e:
    print(f"   [AUTH] Error obteniendo credenciales: {e}")
    credentials, project = None, None

def get_auth_token():
    """Obtener token de autenticación de Google Cloud"""
    try:
        if credentials and not credentials.valid:
            credentials.refresh(Request())
        return credentials.token if credentials else None
    except Exception as e:
        print(f"   [ERROR AUTH] {e}")
        return None

# Historial de alertas
alertas = []
analysis_history = []

# ============================================
# FUNCIONES CLOUD STORAGE
# ============================================

def upload_to_cloud_storage(file_path, destination_blob_name):
    """Sube un archivo a Google Cloud Storage y retorna la URL pública"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(file_path)

        # Hacer el archivo público
        blob.make_public()

        print(f"   [CLOUD] Archivo subido: {blob.public_url}")
        return blob.public_url

    except Exception as e:
        print(f"   [ERROR CLOUD] {e}")
        return None

def analyze_with_vertex_ai(file_gcs_uri, file_type='image'):
    """Analizar archivo con Vertex AI para detección de fuego"""
    try:
        # Verificar que tenemos token de autenticación
        auth_token = get_auth_token()
        if not auth_token:
            print(f"   [VERTEX AI] Sin token de autenticación, saltando análisis")
            return {
                'fire_detected': False,
                'confidence': 0.0,
                'error': 'No authentication token available'
            }

        if file_type == 'image':
            payload = {
                "instances": [{"image_url": file_gcs_uri}]
            }
        else:  # video
            payload = {
                "instances": [{"video_url": file_gcs_uri}],
                "parameters": {
                    "frame_interval": 10,
                    "max_detections": 20,
                    "analyze_audio": True,
                    "audio_top_k": 3
                }
            }

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

        print(f"   [VERTEX AI] Analizando {file_type}: {file_gcs_uri}")
        
        response = requests.post(
            VERTEX_AI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=180
        )

        if response.status_code == 200:
            result = response.json()
            
            # Procesar resultado
            fire_detected = False
            confidence = 0.0
            detections_count = 0
            
            if 'predictions' in result:
                for prediction in result['predictions']:
                    if 'detections' in prediction:
                        for detection in prediction['detections']:
                            if file_type == 'image':
                                for det in detection.get('detections', []):
                                    detections_count += 1
                                    if 'fire' in det.get('class', '').lower() or 'smoke' in det.get('class', '').lower():
                                        fire_detected = True
                                        confidence = max(confidence, det.get('confidence', 0))
                            else:  # video
                                for det in detection.get('detections', []):
                                    detections_count += 1
                                    if 'fire' in det.get('class', '').lower() or 'smoke' in det.get('class', '').lower():
                                        fire_detected = True
                                        confidence = max(confidence, det.get('confidence', 0))
            
            details = {
                'fire_detected': fire_detected,
                'confidence': confidence,
                'detections_count': detections_count,
                'analysis_timestamp': datetime.now().isoformat(),
                'file_type': file_type,
                'gcs_uri': file_gcs_uri
            }
            
            status_msg = "🔥 FUEGO DETECTADO" if fire_detected else "✅ Sin fuego detectado"
            print(f"   [VERTEX AI] {status_msg}: Confianza={confidence:.2%}, Detecciones={detections_count}")
            return details
            
        elif response.status_code == 403:
            print(f"   [VERTEX AI] Sin permisos para acceder al endpoint del equipo")
            return {
                'fire_detected': False,
                'confidence': 0.0,
                'error': 'Insufficient permissions for Vertex AI endpoint'
            }
        else:
            print(f"   [ERROR VERTEX AI] Status: {response.status_code}, {response.text}")
            return {
                'fire_detected': False,
                'confidence': 0.0,
                'error': f'API Error: {response.status_code}'
            }

    except Exception as e:
        print(f"   [ERROR VERTEX AI] {e}")
        return {
            'fire_detected': False,
            'confidence': 0.0,
            'error': str(e)
        }

# ============================================
# FUNCIONES DE CAPTURA
# ============================================

def capture_photo():
    """Captura foto del celular y la sube a Cloud Storage"""
    try:
        url = f"{PHONE_IP}/photo.jpg"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            # Crear directorio temporal local
            os.makedirs("temp_captures", exist_ok=True)
            local_filename = f"temp_captures/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

            with open(local_filename, 'wb') as f:
                f.write(response.content)

            # Subir a Cloud Storage
            cloud_filename = f"photos/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cloud_url = upload_to_cloud_storage(local_filename, cloud_filename)

            # Analizar con Vertex AI
            gcs_uri = f"gs://{BUCKET_NAME}/{cloud_filename}"
            vertex_result = analyze_with_vertex_ai(gcs_uri, 'image')

            # Limpiar archivo temporal
            if os.path.exists(local_filename):
                os.remove(local_filename)

            print(f"   [FOTO] Guardada en Cloud: {cloud_url}")
            
            # Retornar info completa
            return {
                'url': cloud_url,
                'gcs_uri': gcs_uri,
                'vertex_analysis': vertex_result
            }
        return None
    except Exception as e:
        print(f"   [ERROR FOTO] {e}")
        return None

def record_video(duration=5):
    """
    Graba video desde el celular (stream MJPEG) durante N segundos
    y lo convierte a MP4 válido usando FFmpeg, luego lo sube a Cloud Storage.
    """
    try:
        # Crear directorio temporal local
        os.makedirs("temp_captures", exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        raw_file = f"temp_captures/video_{timestamp}.mjpeg"
        final_file = f"temp_captures/video_{timestamp}.mp4"

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

        # Subir a Cloud Storage
        cloud_filename = f"videos/video_{timestamp}.mp4"
        cloud_url = upload_to_cloud_storage(final_file, cloud_filename)

        # Analizar con Vertex AI
        gcs_uri = f"gs://{BUCKET_NAME}/{cloud_filename}"
        vertex_result = analyze_with_vertex_ai(gcs_uri, 'video')

        # Borrar archivos temporales
        for temp_file in [raw_file, final_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        print(f"   [VIDEO] Guardado en Cloud: {cloud_url}")
        
        # Retornar info completa
        return {
            'url': cloud_url,
            'gcs_uri': gcs_uri,
            'vertex_analysis': vertex_result
        }

    except Exception as e:
        print(f"   [ERROR VIDEO] {e}")
        return None

def record_audio(duration=5):
    """
    Graba audio desde el celular durante N segundos,
    lo guarda como WAV y lo convierte a MP3 válido, luego lo sube a Cloud Storage.
    """
    try:
        # Crear directorio temporal local
        os.makedirs("temp_captures", exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        wav_file = f"temp_captures/audio_{timestamp}.wav"
        mp3_file = f"temp_captures/audio_{timestamp}.mp3"

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

        # Subir a Cloud Storage
        cloud_filename = f"audio/audio_{timestamp}.mp3"
        cloud_url = upload_to_cloud_storage(mp3_file, cloud_filename)

        # Limpiar archivos temporales
        for temp_file in [wav_file, mp3_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        print(f"   [AUDIO] Guardado en Cloud: {cloud_url}")
        return cloud_url

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
        <li>GET /camera - Sistema de cámara inteligente</li>
    </ul>
    <p><a href="/camera" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📱 Abrir Cámara Inteligente</a></p>
    """

@app.route('/camera')
def camera_system():
    """Página web del sistema de cámara inteligente"""
    return render_template('camera.html')

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
        
        # Simplemente guardar la alerta - el usuario la verá en el dashboard
        if estado == "alert":
            print("\n>>> ⚠️ ALERTA DETECTADA - Visible en Dashboard <<<")
        
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

@app.route('/upload/photo', methods=['POST'])
def upload_photo():
    """Recibir foto directamente desde el celular"""
    try:
        if 'photo' not in request.files:
            return jsonify({"error": "No se encontró archivo de foto"}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó archivo"}), 400
        
        # Guardar temporalmente
        os.makedirs("temp_captures", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = f"temp_captures/emergency_photo_{timestamp}.jpg"
        file.save(temp_path)
        
        # Subir a Cloud Storage
        cloud_filename = f"photos/emergency_photo_{timestamp}.jpg"
        cloud_url = upload_to_cloud_storage(temp_path, cloud_filename)
        
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        print(f"   [EMERGENCY PHOTO] Recibida desde celular: {cloud_url}")
        
        return jsonify({
            "status": "success",
            "message": "Foto de emergencia recibida",
            "url": cloud_url
        }), 200
        
    except Exception as e:
        print(f"   [ERROR PHOTO] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload/video', methods=['POST'])
def upload_video():
    """Recibir video directamente desde el celular"""
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No se encontró archivo de video"}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó archivo"}), 400
        
        # Guardar temporalmente
        os.makedirs("temp_captures", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = f"temp_captures/emergency_video_{timestamp}.webm"
        file.save(temp_path)
        
        # Subir a Cloud Storage
        cloud_filename = f"videos/emergency_video_{timestamp}.webm"
        cloud_url = upload_to_cloud_storage(temp_path, cloud_filename)
        
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        print(f"   [EMERGENCY VIDEO] Recibido desde celular: {cloud_url}")
        
        return jsonify({
            "status": "success",
            "message": "Video de emergencia recibido",
            "url": cloud_url
        }), 200
        
    except Exception as e:
        print(f"   [ERROR VIDEO] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Recibir audio directamente desde el celular"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No se encontró archivo de audio"}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó archivo"}), 400
        
        # Guardar temporalmente
        os.makedirs("temp_captures", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = f"temp_captures/emergency_audio_{timestamp}.webm"
        file.save(temp_path)
        
        # Subir a Cloud Storage
        cloud_filename = f"audio/emergency_audio_{timestamp}.webm"
        cloud_url = upload_to_cloud_storage(temp_path, cloud_filename)
        
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        print(f"   [EMERGENCY AUDIO] Recibido desde celular: {cloud_url}")
        
        return jsonify({
            "status": "success",
            "message": "Audio de emergencia recibido",
            "url": cloud_url
        }), 200
        
    except Exception as e:
        print(f"   [ERROR AUDIO] {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# ENDPOINTS VERTEX AI Y DASHBOARD
# ============================================

@app.route('/analyze', methods=['POST'])
def analyze_files():
    """Analizar archivos con Vertex AI y enviar notificaciones"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        photo_url = data.get('photo_url')
        video_url = data.get('video_url')
        audio_url = data.get('audio_url')
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "photo_analysis": None,
            "video_analysis": None,
            "fire_detected": False,
            "max_confidence": 0.0
        }
        
        files_info = {}
        
        # Analizar foto con Vertex AI
        if photo_url:
            print(f"   [ANALYZE] Analizando foto: {photo_url}")
            # Convertir URL pública a GCS URI
            gcs_uri = photo_url.replace('https://storage.googleapis.com/', 'gs://')
            photo_result = analyze_image_vertex_ai(gcs_uri)
            results["photo_analysis"] = photo_result
            files_info["photo"] = photo_url
            
            if photo_result and photo_result.get('fire_detected'):
                results["fire_detected"] = True
                results["max_confidence"] = max(results["max_confidence"], photo_result.get('confidence', 0))
        
        # Analizar video con Vertex AI
        if video_url:
            print(f"   [ANALYZE] Analizando video: {video_url}")
            gcs_uri = video_url.replace('https://storage.googleapis.com/', 'gs://')
            video_result = analyze_video_vertex_ai(gcs_uri)
            results["video_analysis"] = video_result
            files_info["video"] = video_url
            
            if video_result and video_result.get('fire_detected'):
                results["fire_detected"] = True
                results["max_confidence"] = max(results["max_confidence"], video_result.get('confidence', 0))
        
        if audio_url:
            files_info["audio"] = audio_url
        
        # Guardar en historial de análisis
        analysis_record = {
            "timestamp": results["timestamp"],
            "files": files_info,
            "results": results,
            "fire_detected": results["fire_detected"],
            "confidence": results["max_confidence"]
        }
        
        analysis_history.append(analysis_record)
        
        # Registrar en consola si se detectó fuego - el usuario lo verá en el dashboard
        if results["fire_detected"]:
            print("   [ALERT] 🔥 FUEGO DETECTADO POR VERTEX AI - Visible en Dashboard")
        
        return jsonify({
            "status": "success",
            "results": results,
            "fire_detected": results["fire_detected"],
            "confidence": results["max_confidence"]
        }), 200
        
    except Exception as e:
        print(f"   [ERROR ANALYZE] {e}")
        return jsonify({"error": str(e)}), 500

def analyze_image_vertex_ai(image_gcs_uri):
    """Analizar imagen usando el endpoint de Vertex AI"""
    try:
        auth_token = get_auth_token()
        if not auth_token:
            return {"error": "No authentication token", "fire_detected": False, "confidence": 0}
        
        payload = {
            "instances": [{"image_url": image_gcs_uri}]
        }
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        print(f"   [VERTEX AI] Enviando imagen para análisis: {image_gcs_uri}")
        
        response = requests.post(
            VERTEX_AI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return process_vertex_response(result, 'image')
        else:
            print(f"   [VERTEX AI ERROR] {response.status_code}: {response.text}")
            return {"error": f"API Error: {response.status_code}", "fire_detected": False, "confidence": 0}
            
    except Exception as e:
        print(f"   [VERTEX AI ERROR] {e}")
        return {"error": str(e), "fire_detected": False, "confidence": 0}

def analyze_video_vertex_ai(video_gcs_uri):
    """Analizar video usando el endpoint de Vertex AI"""
    try:
        auth_token = get_auth_token()
        if not auth_token:
            return {"error": "No authentication token", "fire_detected": False, "confidence": 0}
        
        payload = {
            "instances": [{"video_url": video_gcs_uri}],
            "parameters": {
                "frame_interval": 15,
                "max_detections": 10,
                "analyze_audio": True,
                "audio_top_k": 5
            }
        }
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        print(f"   [VERTEX AI] Enviando video para análisis: {video_gcs_uri}")
        
        response = requests.post(
            VERTEX_AI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            return process_vertex_response(result, 'video')
        else:
            print(f"   [VERTEX AI ERROR] {response.status_code}: {response.text}")
            return {"error": f"API Error: {response.status_code}", "fire_detected": False, "confidence": 0}
            
    except Exception as e:
        print(f"   [VERTEX AI ERROR] {e}")
        return {"error": str(e), "fire_detected": False, "confidence": 0}

def process_vertex_response(result, file_type):
    """Procesar respuesta de Vertex AI"""
    fire_detected = False
    max_confidence = 0.0
    detections_count = 0
    all_detections = []
    
    if 'predictions' in result:
        for prediction in result['predictions']:
            if 'detections' in prediction:
                for detection in prediction.get('detections', []):
                    dets = detection.get('detections', [detection])
                    for det in dets:
                        detections_count += 1
                        class_name = det.get('class', '').lower()
                        confidence = det.get('confidence', 0)
                        
                        all_detections.append({
                            'class': class_name,
                            'confidence': confidence
                        })
                        
                        if 'fire' in class_name or 'smoke' in class_name or 'fuego' in class_name or 'humo' in class_name:
                            fire_detected = True
                            max_confidence = max(max_confidence, confidence)
    
    return {
        'fire_detected': fire_detected,
        'confidence': max_confidence,
        'detections_count': detections_count,
        'detections': all_detections[:10],  # Limitar a 10
        'file_type': file_type,
        'raw_predictions': result.get('predictions', [])
    }

@app.route('/dashboard')
def dashboard():
    """Dashboard para visualizar alertas y resultados"""
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def dashboard_data():
    """Datos para el dashboard"""
    # Contar alertas recientes (últimas 24 horas podría ser útil)
    recent_alerts = [a for a in alertas if a.get('estado') == 'alert']
    
    return jsonify({
        "alertas": alertas[-20:],
        "analysis_history": analysis_history[-20:],
        "total_alertas": len(alertas),
        "total_analysis": len(analysis_history),
        "fires_detected": sum(1 for a in analysis_history if a.get('fire_detected', False)),
        "pending_alerts": len([a for a in alertas[-10:] if a.get('estado') == 'alert'])
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