from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config
from utils.logger import setup_logger
from utils.swagger_spec import SWAGGER_SPEC
import os
import sys

# 导入蓝图
from api.harbor import harbor_bp
from api.docker import docker_bp
from api.system import system_bp

# 初始化日志
logger = setup_logger('app')

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化配置
    config_class.init_app(app)
    
    # 启用 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": config_class.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # 注册蓝图
    app.register_blueprint(harbor_bp)
    app.register_blueprint(docker_bp)
    app.register_blueprint(system_bp)
    
    # Swagger UI 配置
    SWAGGER_URL = '/api/docs'  # Swagger UI 访问路径
    API_URL = '/api/swagger.json'  # Swagger JSON 文件路径

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Harbor Export API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Swagger JSON 路由
    @app.route('/api/swagger.json')
    def swagger_json():
        return jsonify(SWAGGER_SPEC)
    
    # 请求前处理
    @app.before_request
    def before_request():
        """记录请求信息"""
        if request.method != 'OPTIONS':  # 忽略 OPTIONS 请求
            logger.info(f"{request.method} {request.path} - {request.remote_addr}")
    
    # 请求后处理
    @app.after_request
    def after_request(response):
        """添加响应头"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    # 首页路由
    @app.route('/')
    def index():
        """服务首页"""
        return jsonify({
            'name': 'Harbor Image Downloader API',
            'version': '2.0.0',
            'status': 'running',
            'description': '一个功能强大的 Harbor 镜像管理和下载工具',
            'endpoints': {
                'harbor': '/api/harbor/*',
                'docker': '/api/docker/*',
                'system': '/api/system/*'
            },
            'documentation': '/api/docs',
            'health_check': '/api/system/health'
        })
    
    # 错误处理
    @app.errorhandler(400)
    def bad_request(error):
        """400 错误处理"""
        logger.warning(f"Bad Request: {str(error)}")
        return jsonify({
            'success': False,
            'message': '请求参数错误',
            'code': 400,
            'details': str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """404 错误处理"""
        return jsonify({
            'success': False,
            'message': f'接口不存在: {request.path}',
            'code': 404,
            'available_endpoints': {
                'documentation': '/api/docs',
                'health_check': '/api/system/health'
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 错误处理"""
        logger.error(f"Internal Error: {str(error)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'code': 500,
            'details': str(error) if app.debug else None
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """通用异常处理"""
        logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '服务器异常',
            'code': 500,
            'details': str(error) if app.debug else None
        }), 500
    
    return app

def check_dependencies():
    """检查依赖项"""
    logger.info("检查系统依赖...")
    
    # 检查 Docker
    try:
        import docker
        client = docker.from_env()
        client.ping()
        logger.info("✓ Docker 连接正常")
        return True
    except Exception as e:
        logger.error(f"✗ Docker 连接失败: {str(e)}")
        logger.error("请确保 Docker 已安装并正在运行")
        return False

def print_startup_banner():
    """打印启动横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                ---   Harbor EXPORT   V2.0   ---               ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"    🚀 服务启动中...")
    print(f"    📡 监听地址: http://0.0.0.0:5001")
    print(f"    📖 API 文档: http://localhost:5001/api/docs")
    print(f"    ❤️  健康检查: http://localhost:5001/api/system/health")
    print(f"    🐛 调试模式: {'开启' if Config.DEBUG else '关闭'}")
    print(f"    📝 日志文件: {Config.LOG_FILE}")
    print(f"\n    ℹ️  按 Ctrl+C 停止服务\n")
    print("=" * 70)

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    try:
        # 打印启动横幅
        print_startup_banner()
        
        # 检查依赖
        if not check_dependencies():
            logger.warning("依赖检查失败，但仍尝试启动服务...")
        
        # 禁用 SSL 警告（仅用于开发环境）
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        logger.info("=" * 70)
        logger.info("Harbor 镜像下载工具后端服务启动")
        logger.info("=" * 70)
        logger.info(f"Debug 模式: {Config.DEBUG}")
        logger.info(f"监听地址: 0.0.0.0:5001")
        logger.info(f"API 文档: http://localhost:5001/api/docs")
        logger.info(f"CORS 允许来源: {Config.CORS_ORIGINS}")
        logger.info("=" * 70)
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=Config.DEBUG,
            threaded=True,
            use_reloader=Config.DEBUG
        )
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("    👋 服务已停止")
        print("=" * 70)
        logger.info("服务被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {str(e)}", exc_info=True)
        print(f"\n❌ 启动失败: {str(e)}")
        sys.exit(1)
