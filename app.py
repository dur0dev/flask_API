from flask import Flask, jsonify, request
from flasgger import Swagger
from routes.stats_routes import stats_api
from routes.admin_routes import admin_api
from routes.auth_routes import auth_api  # Cambié auth_api por auth_routes
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
import logging
import os;
from datetime import timedelta

# ====================================
# CONFIGURACIÓN DE LOGGING
# ====================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ====================================
# CREAR APLICACIÓN FLASK
# ====================================
app = Flask(__name__)

# ====================================
# CARGAR CONFIGURACIÓN
# ====================================
env = os.environ.get('FLASK_ENV', 'default') # Cambiar por el entorno correspondiente
app.config.from_object(config[env])

# ====================================
# CONFIGURACIÓN DE CORS
# ====================================
# IMPORTANTE: En producción, especifica los orígenes permitidos
CORS(app, 
     origins=app.config['CORS_ORIGINS'],  # Vite usa 5173, CRA usa 3000
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True
)

# ====================================
# CONFIGURACIÓN JWT
# ====================================

# Inicializar JWT Manager
jwt = JWTManager(app)

# ====================================
# MANEJADORES DE ERRORES JWT
# ====================================
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """
    Función que se ejecuta cuando un token ha expirado
    """
    logger.warning("Token expirado detectado")
    return jsonify({
        'msg': 'Token ha expirado',
        'error': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """
    Función que se ejecuta cuando un token es inválido
    """
    logger.warning(f"Token inválido: {error}")
    return jsonify({
        'msg': 'Token inválido',
        'error': 'invalid_token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """
    Función que se ejecuta cuando no se proporciona token
    """
    logger.warning("Token faltante en petición protegida")
    return jsonify({
        'msg': 'Token de autorización requerido',
        'error': 'authorization_required'
    }), 401

@jwt.needs_fresh_token_loader
def token_not_fresh_callback(jwt_header, jwt_payload):
    """
    Función que se ejecuta cuando se necesita un token "fresco"
    """
    return jsonify({
        'msg': 'Token fresco requerido',
        'error': 'fresh_token_required'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    """
    Función que se ejecuta cuando un token ha sido revocado
    """
    return jsonify({
        'msg': 'Token ha sido revocado',
        'error': 'token_revoked'
    }), 401

# ====================================
# CONFIGURACIÓN DE SWAGGER
# ====================================
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "info": {
        "title": "RULEYATEAM API",
        "description": "API oficial para el proyecto ruleyateam",
        "version": "1.0.0",
        "contact": {
            "name": "Equipo de desarrollo",
            "email": "dev@ruleyateam.com"
        }
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header usando Bearer scheme. Ejemplo: 'Bearer {token}'"
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# ====================================
# MANEJADORES DE ERRORES GLOBALES
# ====================================
@app.errorhandler(404)
def not_found(error):
    """
    Manejador para errores 404 (No encontrado)
    """
    return jsonify({
        'error': 'Endpoint no encontrado',
        'message': 'La ruta solicitada no existe'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Manejador para errores 500 (Error interno del servidor)
    """
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({
        'error': 'Error interno del servidor',
        'message': 'Ha ocurrido un error inesperado'
    }), 500

@app.errorhandler(400)
def bad_request(error):
    """
    Manejador para errores 400 (Petición incorrecta)
    """
    return jsonify({
        'error': 'Petición incorrecta',
        'message': 'Los datos enviados no son válidos'
    }), 400

# ====================================
# MIDDLEWARE PARA LOGGING DE REQUESTS
# ====================================
@app.before_request
def log_request_info():
    """
    Log de todas las peticiones recibidas
    """
    logger.info(f"Request: {request.method} {request.url}")

@app.after_request
def log_response_info(response):
    """
    Log de todas las respuestas enviadas
    """
    logger.info(f"Response: {response.status_code}")
    return response

# ====================================
# RUTA DE SALUD (HEALTH CHECK)
# ====================================
@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar que la API está funcionando
    """
    return jsonify({
        'status': 'healthy',
        'message': 'API funcionando correctamente',
        'version': '1.0.0'
    }), 200

# ====================================
# REGISTRAR BLUEPRINTS
# ====================================
app.register_blueprint(stats_api, url_prefix="/api/stats")
app.register_blueprint(admin_api, url_prefix="/api/admin")
app.register_blueprint(auth_api, url_prefix="/api/auth")

# ====================================
# ARRANCAR LA APLICACIÓN
# ====================================
if __name__ == "__main__":
    logger.info("Iniciando servidor Flask...")
    logger.info(f"CORS configurado para orígenes: http://localhost:3000, http://localhost:5173")
    logger.info("Swagger UI disponible en: http://localhost:5000/apidocs/")
    
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',  # Permitir conexiones desde cualquier IP
        port=5000
    )