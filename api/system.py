# ============================================================================
# 文件: api/system.py
# ============================================================================
from flask import Blueprint
from utils.response import success_response, error_response
from utils.logger import setup_logger
from utils.auth_session import require_login
from utils.operation_logger import append as append_oplog, read_lines as read_oplog
import psutil
import os
import shutil
from config import Config

logger = setup_logger('api_system')

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

@system_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        from services.docker_service import DockerService
        docker_service = DockerService()
        docker_connected = docker_service.ping()
        
        return success_response(data={
            'status': 'healthy',
            'docker': 'connected' if docker_connected else 'disconnected'
        })
    except Exception as e:
        return error_response(str(e), 500)

@system_bp.route('/info', methods=['GET'])
@require_login
def system_info():
    """系统信息"""
    try:
        # CPU 信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        # 下载目录信息
        download_dir_size = 0
        if os.path.exists(Config.DOWNLOAD_FOLDER):
            for dirpath, dirnames, filenames in os.walk(Config.DOWNLOAD_FOLDER):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        download_dir_size += os.path.getsize(fp)
        
        return success_response(data={
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            },
            'download_folder': {
                'path': Config.DOWNLOAD_FOLDER,
                'size': download_dir_size
            }
        })
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return error_response(str(e), 500)

@system_bp.route('/cleanup', methods=['POST'])
@require_login
def cleanup_temp_files():
    """清理临时文件"""
    try:
        cleaned_size = 0
        cleaned_count = 0
        
        # 清理下载目录
        if os.path.exists(Config.DOWNLOAD_FOLDER):
            for item in os.listdir(Config.DOWNLOAD_FOLDER):
                item_path = os.path.join(Config.DOWNLOAD_FOLDER, item)
                try:
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                        os.remove(item_path)
                        cleaned_size += size
                        cleaned_count += 1
                    elif os.path.isdir(item_path):
                        size = sum(
                            os.path.getsize(os.path.join(dirpath, filename))
                            for dirpath, dirnames, filenames in os.walk(item_path)
                            for filename in filenames
                        )
                        shutil.rmtree(item_path)
                        cleaned_size += size
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"清理文件失败 {item_path}: {str(e)}")
        
        return success_response(
            data={
                'cleaned_count': cleaned_count,
                'cleaned_size': cleaned_size
            },
            message=f'清理完成，删除 {cleaned_count} 个文件/目录，释放 {cleaned_size / 1024 / 1024:.2f} MB'
        )
    except Exception as e:
        logger.error(f"清理临时文件失败: {str(e)}")
        return error_response(str(e), 500)

@system_bp.route('/logs', methods=['GET'])
@require_login
def get_logs():
    """获取最新日志"""
    try:
        if not os.path.exists(Config.LOG_FILE):
            return success_response(data={'logs': []}, message='日志文件不存在')
        
        # 读取最后 100 行日志
        with open(Config.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-100:] if len(lines) > 100 else lines
        
        return success_response(data={'logs': last_lines})
    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}")
        return error_response(str(e), 500)

@system_bp.route('/record', methods=['POST'])
@require_login
def record_operation():
    try:
        from flask import request
        data = request.get_json() or {}
        # 屏蔽敏感信息
        payload = data.get('payload') or {}
        if 'password' in payload:
            payload['password'] = '******'
        append_oplog({
            'operator': data.get('operator') or request.remote_addr,
            'action': data.get('action') or 'unknown',
            'payload': payload,
            'success': bool(data.get('success', True))
        })
        return success_response(message='记录成功')
    except Exception as e:
        logger.error(f"记录操作失败: {str(e)}")
        return error_response(str(e), 500)

@system_bp.route('/operations', methods=['GET'])
@require_login
def list_operations():
    try:
        from flask import request
        operator = request.args.get('operator')
        logs = read_oplog(limit=1000)
        if operator:
            logs = [l for l in logs if l.get('operator') == operator]
        return success_response(data={'operations': logs})
    except Exception as e:
        logger.error(f"获取操作日志失败: {str(e)}")
        return error_response(str(e), 500)
