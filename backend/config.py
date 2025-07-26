"""
Configuración para la aplicación DataApp1
"""
import os

class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-dataapp1'
    UPLOAD_FOLDER = os.path.abspath('../uploads')
    STATIC_FOLDER = os.path.abspath('../static')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'csv'}

class TestConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.abspath('../test_uploads')
    STATIC_FOLDER = os.path.abspath('../test_static')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
