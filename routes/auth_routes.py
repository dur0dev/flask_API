# auth_routes.py
from flask import Blueprint, request, jsonify, make_response
from db import engine
import pandas as pd
from sqlalchemy import text
import logging
from datetime import datetime
from utils.sql_loader import get_query
from utils.swagger_loader import swagger_doc
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, create_refresh_token, unset_refresh_cookies
import hashlib
from datetime import timedelta

auth_api = Blueprint("auth_api", __name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================
# FUNCIONES AUXILIARES
# ====================================
def hash_password(password):
    """
    Función para hashear contraseñas (si no lo haces en el frontend)
    
    Args:
        password (str): Contraseña en texto plano
        
    Returns:
        str: Hash SHA256 de la contraseña
    """
    return hashlib.sha256(password.encode()).hexdigest()

def login_process(email, password_hash):
    """
    Proceso de verificación de login contra la base de datos
    
    Args:
        email (str): Email del usuario
        password_hash (str): Hash de la contraseña
        
    Returns:
        pandas.DataFrame or None: Datos del usuario si las credenciales son válidas
    """
    try:
        logger.info(f"Verificando credenciales para: {email}")
        
        # Verificar si existe el usuario con esas credenciales
        count_query = pd.read_sql(
            text(get_query('login_query')), 
            engine, 
            params={"email": email, "password_hash": password_hash}
        )
        
        if count_query['count'].iloc[0] > 0:
            logger.info(f"Credenciales válidas para: {email}")
            # Si existe, obtener información del usuario
            user_df = pd.read_sql(
                text(get_query('get_user_info')), 
                engine, 
                params={"email": email, "password_hash": password_hash}
            )
            return user_df
        else:
            logger.warning(f"Credenciales inválidas para: {email}")
            return None
            
    except Exception as e:
        logger.error(f"Error en login_process: {str(e)}")
        return None

# ====================================
# ENDPOINTS DE AUTENTICACIÓN
# ====================================

@auth_api.route("/login", methods=["POST"])
@swagger_doc("login")
def login():
    """
    Endpoint para autenticar usuarios y generar JWT token
    """
    try:
        # Obtener datos del request JSON
        data = request.get_json()
        
        # Validar que se enviaron datos
        if not data:
            logger.warning("Intento de login sin datos JSON")
            return jsonify({"msg": "No se enviaron datos"}), 400
        
        email = data.get("email")
        password = data.get("password")
        
        # Validar que se enviaron los campos requeridos
        if not email or not password:
            logger.warning("Intento de login sin email o password")
            return jsonify({"msg": "Email y contraseña son requeridos"}), 400
        
        # Validación básica de formato de email
        if "@" not in email or "." not in email:
            logger.warning(f"Formato de email inválido: {email}")
            return jsonify({"msg": "Formato de email inválido"}), 400
        
        logger.info(f"Intento de login para: {email}")
        
        # Usar la contraseña tal como viene (ya hasheada desde frontend)
        # Si quieres hashear aquí en el backend, descomenta la siguiente línea:
        # password_hash = hash_password(password)
        password_hash = password  # Mantener si ya hasheas en frontend
        
        # Verificar credenciales contra la base de datos
        user_df = login_process(email, password_hash)
        
        if user_df is None or user_df.empty:
            logger.warning(f"Login fallido para: {email}")
            return jsonify({"msg": "Credenciales inválidas"}), 401
        
        logger.info(f"Login exitoso para: {email}")
        
        # Obtener datos del usuario desde el DataFrame
        user_data = user_df.iloc[0]
        
        # Crear ambos tokens
        access_token = create_access_token(
            identity=email,
            additional_claims={
                "role": user_data.get('user_rol', 'user'),
                "user_id": int(user_data.get('id', 0)) if 'id' in user_data else None,
                "name": user_data.get('username', ''),
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # IMPORTANTE: Configurar el refresh token con expires_delta explícito
        refresh_token = create_refresh_token(
            identity=email,
            expires_delta=timedelta(days=7)  # 7 días explícito
        )

        logger.info(f"Tokens generados para: {email}")

        # Preparar respuesta
        response_data = {
            "token": access_token,
            "user": {
                "email": email,
                "role": user_data.get('user_rol', 'user'),
                "user_id": int(user_data.get('user_id', 0)) if 'user_id' in user_data else None,
                "name": user_data.get('username', '')
            },
            "message": "Login exitoso"
        }

        # IMPORTANTE: Crear respuesta correctamente
        response = make_response(jsonify(response_data))

        # CONFIGURAR COOKIE CON MÁS OPCIONES
        response.set_cookie(
            'refresh_token',
            refresh_token,
            httponly=True,           # No accesible por JavaScript
            secure=False,            # Para desarrollo (HTTP). En producción: True (HTTPS)
            samesite='Lax',          # Cambiar de 'Strict' a 'Lax' para mejor compatibilidad
            max_age=7 * 24 * 60 * 60,  # 7 días en segundos
            path='/'                 # Disponible en toda la aplicación
        )
        
        logger.info(f"Cookie refresh_token configurada para: {email}")
        
        return response, 200
        
    except Exception as e:
        logger.error(f"Error inesperado en endpoint login: {str(e)}")
        return jsonify({"msg": "Error interno del servidor"}), 500
    
@auth_api.route("/verify", methods=["GET"])
@jwt_required()
@swagger_doc("verify_token")
def verify_token():
    """
    Endpoint para verificar si un token JWT es válido
    Se usa cuando el usuario recarga la página para mantener la sesión
    """
    try:
        # Obtener información del token JWT
        current_user_email = get_jwt_identity()
        claims = get_jwt()
        
        logger.info(f"Verificando token para: {current_user_email}")
        
        # Opcional: Verificar en la base de datos que el usuario aún existe y está activo
        try:
            # Verificar que el usuario existe en la base de datos
            # Cambié "usuarios" por "nba.dim_users" para ser consistente
            user_check = pd.read_sql(
                text("SELECT email, username FROM nba.dim_users WHERE email = :email"), 
                engine, 
                params={"email": current_user_email}
            )
            
            if user_check.empty:
                logger.warning(f"Usuario no encontrado en BD durante verificación: {current_user_email}")
                return jsonify({"msg": "Usuario no encontrado"}), 404
                
            # Actualizar información del usuario con datos frescos de la BD
            fresh_user_data = user_check.iloc[0]
            user_info = {
                "email": current_user_email,
                "role": fresh_user_data.get('user_rol', claims.get("role", "user")),
                "user_id": claims.get("id"),
                "name": fresh_user_data.get('username', claims.get("name", ""))
            }
                
        except Exception as db_error:
            logger.error(f"Error al verificar usuario en BD: {str(db_error)}")
            # Si hay error con la BD, usar info del token
            user_info = {
                "email": current_user_email,
                "role": claims.get("role", "user"),
                "user_id": claims.get("user_id"),
                "name": claims.get("name", "")
            }
        
        return jsonify({
            "valid": True,
            "user": user_info,
            "message": "Token válido"
        }), 200
        
    except Exception as e:
        logger.error(f"Error al verificar token: {str(e)}")
        return jsonify({"msg": "Token inválido", "error": "token_verification_failed"}), 401

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, unset_jwt_cookies
from datetime import datetime

@auth_api.route("/logout", methods=["POST"])
@jwt_required()
@swagger_doc("logout")
def logout():
    """
    Endpoint para cerrar sesión del usuario.
    Elimina cookies de JWT (access y refresh) y registra el logout.
    """
    try:
        current_user = get_jwt_identity()
        logger.info(f"Logout solicitado para usuario: {current_user}")

        # Aquí puedes añadir lógica adicional si decides implementar blacklist, etc.
        # Por ejemplo:
        # - Guardar el jti del token en Redis
        # - Registrar el logout en la base de datos

        response = jsonify({
            "msg": "Logout exitoso",
            "user": current_user,
            "logged_out_at": datetime.now().isoformat()
        })

        # Esta función elimina las cookies JWT (access y refresh)
        unset_refresh_cookies(response)

        return response, 200

    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return jsonify({"msg": "Error en logout"}), 500


@auth_api.route("/refresh", methods=["POST"])
def refresh_access_token():
    """
    Endpoint para renovar el access token usando el refresh token
    
    IMPORTANTE: No usar @jwt_required(refresh=True) aquí porque necesitamos
    obtener el refresh token desde las cookies, no desde el header Authorization
    """
    try:
        # PASO 1: Obtener el refresh token desde las cookies
        refresh_token = request.cookies.get('refresh_token')
        
        if not refresh_token:
            logger.warning("No se encontró refresh token en cookies")
            return jsonify({
                "msg": "Refresh token no encontrado",
                "error": "missing_refresh_token"
            }), 401
        
        logger.info("Refresh token encontrado en cookies")
        
        # PASO 2: Verificar y decodificar el refresh token manualmente
        try:
            # Importar jwt para verificación manual
            from flask_jwt_extended import decode_token
            
            # Decodificar el refresh token
            decoded_token = decode_token(refresh_token)
            current_user_email = decoded_token['sub']  # 'sub' contiene la identidad
            
            logger.info(f"Renovando access token para: {current_user_email}")
            
        except Exception as token_error:
            logger.error(f"Error decodificando refresh token: {str(token_error)}")
            return jsonify({
                "msg": "Refresh token inválido o expirado",
                "error": "invalid_refresh_token"
            }), 401

        # PASO 3: Verificar que el usuario aún existe en la BD
        try:
            user_check = pd.read_sql(
                text("SELECT email, user_rol, username, id FROM nba.dim_users WHERE email = :email"), 
                engine, 
                params={"email": current_user_email}
            )
            
            if user_check.empty:
                logger.warning(f"Usuario no encontrado durante refresh: {current_user_email}")
                return jsonify({"msg": "Usuario no encontrado"}), 404
                
            user_data = user_check.iloc[0]
            
        except Exception as db_error:
            logger.error(f"Error BD durante refresh: {str(db_error)}")
            return jsonify({"msg": "Error interno del servidor"}), 500

        # PASO 4: Crear nuevo access token con información actualizada
        new_access_token = create_access_token(
            identity=current_user_email,
            additional_claims={
                "role": user_data.get('user_rol', 'user'),
                "user_id": int(user_data.get('id', 0)) if 'id' in user_data else None,
                "name": user_data.get('username', ''),
                "refreshed_at": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Nuevo access token generado para: {current_user_email}")

        # PASO 5: Respuesta con el nuevo token
        return jsonify({
            "token": new_access_token,
            "user": {
                "email": current_user_email,
                "role": user_data.get('user_rol', 'user'),
                "user_id": int(user_data.get('user_id', 0)) if 'user_id' in user_data else None,
                "name": user_data.get('name', '')
            },
            "message": "Access token renovado correctamente"
        }), 200

    except Exception as e:
        logger.error(f"Error inesperado al renovar token: {str(e)}")
        return jsonify({
            "msg": "Error interno del servidor",
            "error": "refresh_failed"
        }), 500
