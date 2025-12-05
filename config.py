"""
应用配置文件
支持从环境变量和 .env 文件读取配置
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载 .env 文件
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """应用配置基类"""
    
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    TESTING = False
    
    # CORS 配置
    CORS_ORIGINS_STR = os.environ.get('CORS_ORIGINS', '*')
    CORS_ORIGINS = CORS_ORIGINS_STR.split(',') if CORS_ORIGINS_STR != '*' else '*'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024 * 1024))  # 默认 16GB
    UPLOAD_FOLDER = os.path.join(basedir, os.environ.get('UPLOAD_FOLDER', 'temp'))
    DOWNLOAD_FOLDER = os.path.join(basedir, os.environ.get('DOWNLOAD_FOLDER', 'downloads'))
    
    # Docker 配置
    DOCKER_REGISTRY_INSECURE = os.environ.get('DOCKER_REGISTRY_INSECURE', 'True').lower() == 'true'
    DOCKER_TIMEOUT = int(os.environ.get('DOCKER_TIMEOUT', 600))
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(basedir, os.environ.get('LOG_FILE', 'logs/app.log'))
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 默认 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Harbor API 配置
    HARBOR_API_VERSION = os.environ.get('HARBOR_API_VERSION', 'v2.0')
    HARBOR_REQUEST_TIMEOUT = int(os.environ.get('HARBOR_REQUEST_TIMEOUT', 30))
    
    # 服务器配置
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    SERVER_THREADED = os.environ.get('SERVER_THREADED', 'True').lower() == 'true'
    
    # 会话配置
    SESSION_LIFETIME = timedelta(hours=24)
    
    # 测试环境 Harbor 配置（仅用于测试）
    TEST_HARBOR_URL = os.environ.get('TEST_HARBOR_URL', 'https://10.3.2.40')
    TEST_HARBOR_USERNAME = os.environ.get('TEST_HARBOR_USERNAME', 'admin')
    TEST_HARBOR_PASSWORD = os.environ.get('TEST_HARBOR_PASSWORD', 'Harbor12345')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    
    @classmethod
    def get_config_info(cls):
        """获取配置信息（用于调试）"""
        return {
            'debug': cls.DEBUG,
            'testing': cls.TESTING,
            'cors_origins': cls.CORS_ORIGINS,
            'docker_timeout': cls.DOCKER_TIMEOUT,
            'log_level': cls.LOG_LEVEL,
            'harbor_api_version': cls.HARBOR_API_VERSION,
            'server_host': cls.SERVER_HOST,
            'server_port': cls.SERVER_PORT,
            'upload_folder': cls.UPLOAD_FOLDER,
            'download_folder': cls.DOWNLOAD_FOLDER
        }


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 测试用的临时目录
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'test_temp')
    DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'test_downloads')
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'test_logs', 'test.log')


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    
    # 生产环境必须设置 SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
    
    # 生产环境必须指定具体的 CORS 来源
    if Config.CORS_ORIGINS == '*':
        raise ValueError("生产环境不能使用 CORS_ORIGINS=*，必须指定具体域名")


# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}