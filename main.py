# main.py - Punto de entrada para Google App Engine
import os
from server import app

if __name__ == '__main__':
    # App Engine asigna el puerto automáticamente
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)