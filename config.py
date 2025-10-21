import os
from datetime import timedelta

class Config:
    """
    Clase de configuración para la aplicación Flask
    """
    
    # ====================================
    # CONFIGURACIÓN GENERAL
    # ====================================
    # Clave secreta para JWT y sesiones
    # IMPORTANTE: En producción, usar una variable de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-super-secreta-aqui-cambiar-en-produccion'
    
    # ====================================
    # CONFIGURACIÓN JWT
    # ====================================
    # Clave secreta específica para JWT (puede ser la misma que SECRET_KEY)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    
    # Duración del token de acceso
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=20)
    
    # Algoritmo de encriptación
    JWT_ALGORITHM = 'HS256'
    
    # Header donde se envía el token
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    JWT_TOKEN_LOCATION= ['headers','cookies']
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'
    
    # ====================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # ====================================
    # Aquí puedes añadir tu configuración de BD si la necesitas
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
    # ====================================
    # CONFIGURACIÓN DE CORS
    # ====================================
    # Orígenes permitidos (para producción, especificar dominios exactos)
    CORS_ORIGINS = [
        'http://localhost:3000',  # React (Create React App)
        'http://localhost:5173',  # Vite
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173'
    ]
    
    # ====================================
    # CONFIGURACIÓN DE DESARROLLO
    # ====================================
    DEBUG = True  # Cambiar a False en producción
    TESTING = False

class ProductionConfig(Config):
    """
    Configuración para producción
    """
    DEBUG = False
    TESTING = False
    
    # En producción, usar variables de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Orígenes CORS más restrictivos
    CORS_ORIGINS = [
        'https://tu-dominio-frontend.com'
    ]

class DevelopmentConfig(Config):
    """
    Configuración para desarrollo
    """
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """
    Configuración para testing
    """
    DEBUG = False
    TESTING = True
    
    # Token de duración más corta para tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)

# ====================================
# SELECTOR DE CONFIGURACIÓN
# ====================================
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}