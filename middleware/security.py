from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt, get_jwt_identity
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

# ====================================
# RATE LIMITING SIMPLE
# ====================================
# Diccionario para guardar intentos por IP
request_counts = defaultdict(list)

def rate_limit(max_requests=10, per_seconds=60):
    """
    Decorador para limitar el número de peticiones por IP
    
    Args:
        max_requests: Número máximo de peticiones
        per_seconds: En cuántos segundos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener IP del cliente
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            current_time = time.time()
            
            # Limpiar peticiones antiguas
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip] 
                if current_time - req_time < per_seconds
            ]
            
            # Verificar límite
            if len(request_counts[client_ip]) >= max_requests:
                logger.warning(f"Rate limit excedido para IP: {client_ip}")
                return jsonify({
                    'error': 'Demasiadas peticiones',
                    'message': f'Máximo {max_requests} peticiones por {per_seconds} segundos'
                }), 429
            
            # Registrar petición actual
            request_counts[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ====================================
# VALIDADOR DE ROLES
# ====================================
def require_role(required_role):
    """
    Decorador para requerir un rol específico
    
    Args:
        required_role: El rol requerido ('admin', 'user', etc.)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener claims del JWT
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role != required_role:
                logger.warning(f"Acceso denegado. Usuario con rol '{user_role}' intentó acceder a endpoint que requiere '{required_role}'")
                return jsonify({
                    'error': 'Permisos insuficientes',
                    'message': f'Se requiere rol: {required_role}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ====================================
# VALIDADOR DE HEADERS DE SEGURIDAD
# ====================================
def validate_request_headers(f):
    """
    Decorador para validar headers importantes de seguridad
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar Content-Type en peticiones POST/PUT
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({
                    'error': 'Content-Type inválido',
                    'message': 'Se requiere Content-Type: application/json'
                }), 400
        
        return f(*args, **kwargs)
    return decorated_function

# ====================================
# LOGGING DE SEGURIDAD
# ====================================
def log_security_event(event_type, details=None):
    """
    Función para log de eventos de seguridad
    
    Args:
        event_type: Tipo de evento ('login_attempt', 'token_expired', etc.)
        details: Detalles adicionales
    """
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_data = {
        'event': event_type,
        'ip': client_ip,
        'user_agent': user_agent,
        'timestamp': time.time(),
        'details': details or {}
    }
    
    logger.info(f"Security Event: {log_data}")

# ====================================
# EJEMPLO DE USO EN TUS ENDPOINTS
# ====================================
"""
# En auth_routes.py:

from middleware.security import rate_limit, require_role, validate_request_headers, log_security_event

@auth_api.route("/login", methods=["POST"])
@rate_limit(max_requests=5, per_seconds=300)  # 5 intentos por 5 minutos
@validate_request_headers
def login():
    # tu código de login...
    log_security_event('login_attempt', {'email': email, 'success': success})
    # resto del código...

@auth_api.route("/admin-only", methods=["GET"])
@jwt_required()
@require_role('admin')
def admin_endpoint():
    # Solo usuarios con rol 'admin' pueden acceder
    pass
"""