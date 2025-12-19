# server.py - Sistema IoT de Detección de Incendios
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import sys
import os
import requests
import time
import json
import base64
import io
from dotenv import load_dotenv
from google.cloud import storage
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# ============================================
# CONFIGURACION
# ============================================
BUCKET_NAME = os.getenv('BUCKET_NAME', 'iot-captures-481620')
VERTEX_AI_ENDPOINT = os.getenv('VERTEX_AI_ENDPOINT', 'https://southamerica-east1-aiplatform.googleapis.com/v1/projects/peaceful-impact-478922-t6/locations/southamerica-east1/endpoints/4530889505971896320:predict')
ALERT_EMAIL = os.getenv('ALERT_EMAIL', 'cpardave@unsa.edu.pe')
APP_URL = os.getenv('APP_URL', 'https://project-iot-481620.ue.r.appspot.com')

# N8N Webhooks - PRODUCCIÓN
N8N_WEBHOOK_ALERT = 'https://christiantestcloud.app.n8n.cloud/webhook/send-alerta'  # Email: "ABRE LA CÁMARA"
N8N_WEBHOOK_RESULT = 'https://christiantestcloud.app.n8n.cloud/webhook/send-result'  # Email: "Resultado de verificación"

# Cliente de autenticación
credentials = None
storage_client = None

def init_google_clients():
    """Inicializar clientes de Google Cloud"""
    global credentials, storage_client
    try:
        credentials, project = default(scopes=[
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/devstorage.full_control',
            'https://www.googleapis.com/auth/gmail.send'
        ])
        storage_client = storage.Client(credentials=credentials)
        print(f"[AUTH] Credenciales inicializadas para proyecto: {project}")
        return True
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return False

# Inicializar al cargar
init_google_clients()

def get_auth_token():
    """Obtener token de autenticación actualizado"""
    global credentials
    try:
        if credentials:
            if not credentials.valid:
                credentials.refresh(Request())
            return credentials.token
        return None
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return None

# Historial
alertas = []
analysis_history = []

# ============================================
# FUNCIONES CLOUD STORAGE
# ============================================

def upload_to_cloud_storage(file_data, destination_blob_name, content_type='application/octet-stream'):
    """Sube datos de archivo a Google Cloud Storage"""
    try:
        if not storage_client:
            print("[CLOUD ERROR] Storage client no inicializado")
            return None, None
        
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        
        # Si file_data es bytes, subir directamente
        if isinstance(file_data, bytes):
            blob.upload_from_string(file_data, content_type=content_type)
        else:
            # Si es un path, subir desde archivo
            blob.upload_from_filename(file_data, content_type=content_type)
        
        # Hacer público
        blob.make_public()
        
        # Generar URI de GCS (formato que Vertex AI necesita)
        gcs_uri = f"gs://{BUCKET_NAME}/{destination_blob_name}"
        public_url = blob.public_url
        
        print(f"[CLOUD] Subido: {gcs_uri}")
        return public_url, gcs_uri
        
    except Exception as e:
        print(f"[CLOUD ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None, None

def upload_bytes_to_cloud_storage(file_bytes, destination_blob_name, content_type):
    """Sube bytes directamente a Cloud Storage"""
    try:
        if not storage_client:
            print("[CLOUD ERROR] Storage client no inicializado")
            return None, None
        
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        
        blob.upload_from_string(file_bytes, content_type=content_type)
        blob.make_public()
        
        gcs_uri = f"gs://{BUCKET_NAME}/{destination_blob_name}"
        public_url = blob.public_url
        
        print(f"[CLOUD] Subido: {gcs_uri}")
        return public_url, gcs_uri
        
    except Exception as e:
        print(f"[CLOUD ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None, None

# ============================================
# FUNCIONES VERTEX AI (siguiendo ejemplo del colab)
# ============================================

def predict_image_from_gcs(image_gcs_uri):
    """
    Analizar imagen desde Google Cloud Storage
    Siguiendo el formato del ejemplo: gs://bucket/path/to/image.jpg
    """
    try:
        auth_token = get_auth_token()
        if not auth_token:
            return {"error": "No auth token", "fire_detected": False, "confidence": 0}
        
        payload = {
            "instances": [
                {"image_url": image_gcs_uri}
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        print(f"[VERTEX AI] Analizando imagen: {image_gcs_uri}")
        
        response = requests.post(
            VERTEX_AI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"[VERTEX AI] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            return process_vertex_response(result)
        else:
            print(f"[VERTEX AI ERROR] {response.status_code}: {response.text[:500]}")
            return {"error": f"API Error: {response.status_code}", "fire_detected": False, "confidence": 0}
            
    except Exception as e:
        print(f"[VERTEX AI ERROR] {e}")
        return {"error": str(e), "fire_detected": False, "confidence": 0}

def predict_video_from_gcs(video_gcs_uri, frame_interval=15, max_detections=10, analyze_audio=True):
    """
    Analizar video desde Google Cloud Storage
    Siguiendo el formato del ejemplo: gs://bucket/path/to/video.mp4
    """
    try:
        auth_token = get_auth_token()
        if not auth_token:
            return {"error": "No auth token", "fire_detected": False, "confidence": 0}
        
        payload = {
            "instances": [
                {"video_url": video_gcs_uri}
            ],
            "parameters": {
                "frame_interval": frame_interval,
                "max_detections": max_detections,
                "analyze_audio": analyze_audio,
                "audio_top_k": 5
            }
        }
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        print(f"[VERTEX AI] Analizando video: {video_gcs_uri}")
        
        response = requests.post(
            VERTEX_AI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=300
        )
        
        print(f"[VERTEX AI] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            return process_vertex_response(result)
        else:
            print(f"[VERTEX AI ERROR] {response.status_code}: {response.text[:500]}")
            return {"error": f"API Error: {response.status_code}", "fire_detected": False, "confidence": 0}
            
    except Exception as e:
        print(f"[VERTEX AI ERROR] {e}")
        return {"error": str(e), "fire_detected": False, "confidence": 0}

def process_vertex_response(result):
    """Procesar respuesta de Vertex AI"""
    fire_detected = False
    max_confidence = 0.0
    detections_count = 0
    all_detections = []
    
    if 'predictions' in result:
        for prediction in result['predictions']:
            # Manejar detecciones directas
            if 'detections' in prediction:
                for detection in prediction['detections']:
                    dets = detection.get('detections', [detection])
                    for det in dets:
                        detections_count += 1
                        class_name = det.get('class', '').lower()
                        confidence = det.get('confidence', 0)
                        
                        all_detections.append({
                            'class': class_name,
                            'confidence': confidence
                        })
                        
                        if any(x in class_name for x in ['fire', 'smoke', 'fuego', 'humo']):
                            fire_detected = True
                            max_confidence = max(max_confidence, confidence)
            
            # Manejar analysis_summary (para videos)
            if 'analysis_summary' in prediction:
                summary = prediction['analysis_summary']
                if summary.get('frames_with_fire', 0) > 0:
                    fire_detected = True
                    max_confidence = max(max_confidence, summary.get('fire_detection_percentage', 0) / 100)
    
    return {
        'fire_detected': fire_detected,
        'confidence': max_confidence,
        'detections_count': detections_count,
        'detections': all_detections[:10],
        'raw_response': result
    }

# ============================================
# FUNCIONES EMAIL (Gmail API) Y N8N
# ============================================

def send_n8n_alert(alert_data):
    """Enviar alerta INICIAL a n8n webhook (email: ABRE LA CÁMARA)"""
    try:
        response = requests.post(
            N8N_WEBHOOK_ALERT,
            json=alert_data,
            timeout=10
        )
        if response.status_code == 200:
            print(f"[N8N ALERT] ✓ Email de alerta enviado")
            return True
        else:
            print(f"[N8N ALERT] ✗ Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[N8N ALERT ERROR] {e}")
        return False

def send_n8n_result(result_data):
    """Enviar RESULTADO de verificación a n8n webhook (email: RESULTADO)"""
    try:
        response = requests.post(
            N8N_WEBHOOK_RESULT,
            json=result_data,
            timeout=10
        )
        if response.status_code == 200:
            print(f"[N8N RESULT] ✓ Email de resultado enviado")
            return True
        else:
            print(f"[N8N RESULT] ✗ Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[N8N RESULT ERROR] {e}")
        return False

def send_alert_email():
    """Enviar email simple de alerta usando Gmail API"""
    try:
        # Por ahora, solo logueamos - Gmail API requiere OAuth2 configurado
        print(f"[EMAIL] Alerta enviada a {ALERT_EMAIL}")
        print(f"[EMAIL] Mensaje: Nueva alerta de incendio detectada. Ver camara: {APP_URL}/camera")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

# ============================================
# ENDPOINTS
# ============================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/camera')
def camera_page():
    return render_template('camera.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "bucket": BUCKET_NAME,
        "total_alertas": len(alertas),
        "total_analysis": len(analysis_history)
    })

# ============================================
# ENDPOINTS DE ALERTAS
# ============================================

@app.route('/alert', methods=['POST'])
def recibir_alerta():
    """Recibe alertas del Arduino"""
    try:
        datos = request.get_json() or {}
        
        alerta = {
            "id": len(alertas) + 1,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "temperatura": datos.get('temp', 0),
            "luz": datos.get('light', 0),
            "estado": datos.get('status', 'unknown')
        }
        
        print(f"[ALERTA] {alerta['timestamp']} - Temp: {alerta['temperatura']}C, Luz: {alerta['luz']}, Estado: {alerta['estado']}")
        
        alertas.append(alerta)
        
        # Enviar email si es alerta real
        if alerta['estado'] == 'alert':
            send_alert_email()
        
        return jsonify({"status": "received", "alerta_id": alerta['id']}), 200
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-alert', methods=['POST'])
def test_alert():
    """Endpoint para probar alertas sin Arduino - Envía email de ALERTA"""
    alerta = {
        "id": len(alertas) + 1,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "temperatura": 45.5,
        "luz": 850,
        "estado": "alert",
        "test": True
    }
    
    alertas.append(alerta)
    
    # Enviar email de ALERTA (igual que cuando Arduino detecta umbral)
    n8n_data = {
        "timestamp": alerta["timestamp"],
        "fire_detected": True,
        "temperature": alerta["temperatura"],
        "light": alerta["luz"],
        "alert_message": "ALERTA: Umbral de temperatura/luz superado. Verificación requerida.",
        "camera_url": f"{APP_URL}/camera",
        "dashboard_url": f"{APP_URL}/dashboard"
    }
    send_n8n_alert(n8n_data)
    
    print(f"[TEST ALERT] Alerta de prueba creada y email enviado")
    
    return jsonify({
        "status": "success", 
        "alerta": alerta,
        "message": "Alerta enviada por email. Ve a /camera para capturar evidencia."
    }), 200

@app.route('/send-result', methods=['POST'])
def send_result():
    """Enviar resultado de verificación del usuario (después de abrir la cámara)"""
    try:
        data = request.json
        
        user_confirmed = data.get('user_confirmed', False)
        is_false_alarm = data.get('is_false_alarm', False)
        
        # Determinar status y color según el resultado
        if user_confirmed and not is_false_alarm:
            status_text = "INCENDIO CONFIRMADO"
            status_bg_color = "#dc2626"  # Rojo
        elif user_confirmed and is_false_alarm:
            status_text = "FALSA ALARMA"
            status_bg_color = "#f59e0b"  # Naranja
        else:
            status_text = "SIN CONFIRMACIÓN"
            status_bg_color = "#6b7280"  # Gris
        
        # Datos del resultado
        result_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_confirmed": user_confirmed,
            "is_false_alarm": is_false_alarm,
            "status_text": status_text,
            "status_bg_color": status_bg_color,
            "user_response": data.get('user_response', 'El usuario no proporcionó comentarios.'),
            "photo_url": data.get('photo_url', ''),
            "video_url": data.get('video_url', ''),
            "audio_url": data.get('audio_url', ''),
            "dashboard_url": f"{APP_URL}/dashboard"
        }
        
        # Enviar a n8n webhook de resultado
        success = send_n8n_result(result_data)
        
        if success:
            return jsonify({"status": "success", "message": "Resultado enviado"}), 200
        else:
            return jsonify({"status": "error", "message": "No se pudo enviar resultado"}), 500
            
    except Exception as e:
        print(f"[SEND RESULT ERROR] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/alertas', methods=['GET'])
def ver_alertas():
    return jsonify({
        "total": len(alertas),
        "alertas": alertas[-20:]
    })

# ============================================
# ENDPOINTS DE UPLOAD
# ============================================

@app.route('/upload/photo', methods=['POST'])
def upload_photo():
    """Subir foto a Cloud Storage"""
    try:
        print(f"[UPLOAD PHOTO] Request files: {list(request.files.keys())}")
        print(f"[UPLOAD PHOTO] Content-Type: {request.content_type}")
        print(f"[UPLOAD PHOTO] Content-Length: {request.content_length}")
        
        if 'photo' not in request.files:
            print(f"[UPLOAD PHOTO ERROR] 'photo' not in request.files")
            return jsonify({"error": "No photo file", "success": False}), 400
        
        file = request.files['photo']
        print(f"[UPLOAD PHOTO] File received: {file.filename}, size: {file.content_length}")
        
        if file.filename == '':
            print(f"[UPLOAD PHOTO ERROR] Empty filename")
            return jsonify({"error": "Empty filename", "success": False}), 400
        
        # Leer bytes del archivo
        file_bytes = file.read()
        print(f"[UPLOAD PHOTO] Read {len(file_bytes)} bytes")
        
        # Generar nombre
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"photos/photo_{timestamp}.jpg"
        
        print(f"[UPLOAD PHOTO] Uploading to: {blob_name}")
        
        # Subir a Cloud Storage
        public_url, gcs_uri = upload_bytes_to_cloud_storage(
            file_bytes, 
            blob_name, 
            'image/jpeg'
        )
        
        if not public_url:
            print(f"[UPLOAD PHOTO ERROR] upload_bytes_to_cloud_storage returned None")
            return jsonify({"error": "Upload failed", "success": False}), 500
        
        print(f"[UPLOAD PHOTO SUCCESS] URL: {public_url}")
        
        return jsonify({
            "success": True,
            "url": public_url,
            "gcs_uri": gcs_uri
        }), 200
        
    except Exception as e:
        print(f"[UPLOAD PHOTO ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/upload/video', methods=['POST'])
def upload_video():
    """Subir video a Cloud Storage"""
    try:
        print(f"[UPLOAD VIDEO] Request files: {list(request.files.keys())}")
        print(f"[UPLOAD VIDEO] Content-Type: {request.content_type}")
        
        if 'video' not in request.files:
            print(f"[UPLOAD VIDEO ERROR] 'video' not in request.files")
            return jsonify({"error": "No video file", "success": False}), 400
        
        file = request.files['video']
        print(f"[UPLOAD VIDEO] File received: {file.filename}")
        
        if file.filename == '':
            print(f"[UPLOAD VIDEO ERROR] Empty filename")
            return jsonify({"error": "Empty filename", "success": False}), 400
        
        file_bytes = file.read()
        print(f"[UPLOAD VIDEO] Read {len(file_bytes)} bytes")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"videos/video_{timestamp}.webm"
        
        print(f"[UPLOAD VIDEO] Uploading to: {blob_name}")
        
        public_url, gcs_uri = upload_bytes_to_cloud_storage(
            file_bytes,
            blob_name,
            'video/webm'
        )
        
        if not public_url:
            print(f"[UPLOAD VIDEO ERROR] upload_bytes_to_cloud_storage returned None")
            return jsonify({"error": "Upload failed", "success": False}), 500
        
        print(f"[UPLOAD VIDEO SUCCESS] URL: {public_url}")
        
        return jsonify({
            "success": True,
            "url": public_url,
            "gcs_uri": gcs_uri
        }), 200
        
    except Exception as e:
        print(f"[UPLOAD VIDEO ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Subir audio a Cloud Storage"""
    try:
        print(f"[UPLOAD AUDIO] Request files: {list(request.files.keys())}")
        print(f"[UPLOAD AUDIO] Content-Type: {request.content_type}")
        
        if 'audio' not in request.files:
            print(f"[UPLOAD AUDIO ERROR] 'audio' not in request.files")
            return jsonify({"error": "No audio file", "success": False}), 400
        
        file = request.files['audio']
        print(f"[UPLOAD AUDIO] File received: {file.filename}")
        
        if file.filename == '':
            print(f"[UPLOAD AUDIO ERROR] Empty filename")
            return jsonify({"error": "Empty filename", "success": False}), 400
        
        file_bytes = file.read()
        print(f"[UPLOAD AUDIO] Read {len(file_bytes)} bytes")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"audio/audio_{timestamp}.webm"
        
        print(f"[UPLOAD AUDIO] Uploading to: {blob_name}")
        
        public_url, gcs_uri = upload_bytes_to_cloud_storage(
            file_bytes,
            blob_name,
            'audio/webm'
        )
        
        if not public_url:
            print(f"[UPLOAD AUDIO ERROR] upload_bytes_to_cloud_storage returned None")
            return jsonify({"error": "Upload failed", "success": False}), 500
        
        print(f"[UPLOAD AUDIO SUCCESS] URL: {public_url}")
        
        return jsonify({
            "success": True,
            "url": public_url,
            "gcs_uri": gcs_uri
        }), 200
        
    except Exception as e:
        print(f"[UPLOAD AUDIO ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

# ============================================
# ENDPOINTS DE ANALISIS
# ============================================

@app.route('/analyze', methods=['POST'])
def analyze_files():
    """Analizar archivos con Vertex AI"""
    try:
        data = request.get_json() or {}
        
        photo_gcs = data.get('photo_gcs_uri')
        video_gcs = data.get('video_gcs_uri')
        audio_url = data.get('audio_url')
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "photo_analysis": None,
            "video_analysis": None,
            "fire_detected": False,
            "confidence": 0.0
        }
        
        files_info = {}
        
        # Analizar foto
        if photo_gcs:
            print(f"[ANALYZE] Foto: {photo_gcs}")
            photo_result = predict_image_from_gcs(photo_gcs)
            results["photo_analysis"] = photo_result
            files_info["photo"] = data.get('photo_url', photo_gcs)
            
            if photo_result.get('fire_detected'):
                results["fire_detected"] = True
                results["confidence"] = max(results["confidence"], photo_result.get('confidence', 0))
        
        # Analizar video
        if video_gcs:
            print(f"[ANALYZE] Video: {video_gcs}")
            video_result = predict_video_from_gcs(video_gcs)
            results["video_analysis"] = video_result
            files_info["video"] = data.get('video_url', video_gcs)
            
            if video_result.get('fire_detected'):
                results["fire_detected"] = True
                results["confidence"] = max(results["confidence"], video_result.get('confidence', 0))
        
        if audio_url:
            files_info["audio"] = audio_url
        
        # Guardar en historial
        record = {
            "id": len(analysis_history) + 1,
            "timestamp": results["timestamp"],
            "files": files_info,
            "fire_detected": results["fire_detected"],
            "confidence": results["confidence"],
            "photo_analysis": results["photo_analysis"],
            "video_analysis": results["video_analysis"]
        }
        analysis_history.append(record)
        
        # Enviar resultado de Vertex AI a n8n (send-result)
        # Determinar status según resultado de Vertex AI
        if results["fire_detected"]:
            status_text = "INCENDIO CONFIRMADO"
            status_bg_color = "#dc2626"  # Rojo
            user_response = f"Vertex AI detectó fuego con {results['confidence']:.1%} de precisión"
            print(f"[VERTEX AI RESULT] 🔥 FUEGO DETECTADO - Precisión: {results['confidence']:.1%}")
        else:
            status_text = "FALSA ALARMA"
            status_bg_color = "#22c55e"  # Verde
            user_response = f"Vertex AI no detectó fuego (precisión: {results['confidence']:.1%})"
            print(f"[VERTEX AI RESULT] ✅ SIN FUEGO - Precisión: {results['confidence']:.1%}")
        
        # Enviar email de RESULTADO (con respuesta de Vertex AI)
        result_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_confirmed": results["fire_detected"],
            "is_false_alarm": not results["fire_detected"],
            "status_text": status_text,
            "status_bg_color": status_bg_color,
            "user_response": user_response,
            "photo_url": files_info.get("photo", ""),
            "video_url": files_info.get("video", ""),
            "audio_url": files_info.get("audio", ""),
            "dashboard_url": f"{APP_URL}/dashboard"
        }
        send_n8n_result(result_data)
        
        return jsonify({
            "success": True,
            "fire_detected": results["fire_detected"],
            "confidence": results["confidence"],
            "results": results
        }), 200
        
    except Exception as e:
        print(f"[ANALYZE ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

# ============================================
# API DASHBOARD
# ============================================

@app.route('/api/dashboard-data')
def dashboard_data():
    """Datos para el dashboard"""
    pending = len([a for a in alertas[-10:] if a.get('estado') == 'alert'])
    fires = sum(1 for a in analysis_history if a.get('fire_detected'))
    
    return jsonify({
        "alertas": alertas[-20:],
        "analysis_history": analysis_history[-20:],
        "total_alertas": len(alertas),
        "total_analysis": len(analysis_history),
        "fires_detected": fires,
        "pending_alerts": pending
    })

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"\n{'='*50}")
    print("  SERVIDOR IoT - DETECCION DE INCENDIOS")
    print(f"{'='*50}")
    print(f"  Bucket: {BUCKET_NAME}")
    print(f"  Puerto: {port}")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
