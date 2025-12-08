from flask import Blueprint, send_file, request
from services.docker_service import DockerService
from utils.response import success_response, error_response
from utils.auth import require_harbor_config
from utils.logger import setup_logger
import os

logger = setup_logger('api_docker')

docker_bp = Blueprint('docker', __name__, url_prefix='/api/docker')

# 全局 Docker 服务实例
docker_service = None

def get_docker_service():
    """获取 Docker 服务实例"""
    global docker_service
    if docker_service is None:
        docker_service = DockerService()
    return docker_service

@docker_bp.route('/ping', methods=['GET'])
def ping():
    """检查 Docker 连接"""
    try:
        service = get_docker_service()
        if service.ping():
            return success_response(message='Docker 连接正常')
        else:
            return error_response('Docker 连接失败', 500)
    except Exception as e:
        logger.error(f"Docker ping 失败: {str(e)}")
        return error_response(str(e), 500)

@docker_bp.route('/download', methods=['POST'])
@require_harbor_config
def download_image():
    """下载镜像"""
    try:
        data = request.get_json()
        image_name = data.get('image')
        tag = data.get('tag', 'latest')
        
        if not image_name:
            return error_response('缺少 image 参数', 400)
        
        # 分离 image 和 tag
        if ':' in image_name:
            image_name, tag = image_name.rsplit(':', 1)
        
        service = get_docker_service()
        
        result = service.download_image(
            data['harborUrl'],
            data['username'],
            data['password'],
            image_name,
            tag
        )
        
        # 返回文件
        return send_file(
            result['path'],
            mimetype='application/gzip',
            as_attachment=True,
            download_name=result['filename']
        )
        
    except Exception as e:
        logger.error(f"下载镜像失败: {str(e)}")
        return error_response(str(e), 500)

@docker_bp.route('/local-images', methods=['GET'])
def get_local_images():
    """获取本地镜像列表"""
    try:
        service = get_docker_service()
        images = service.get_local_images()
        return success_response(data={'images': images})
    except Exception as e:
        logger.error(f"获取本地镜像失败: {str(e)}")
        return error_response(str(e), 500)

@docker_bp.route('/remove-image', methods=['POST'])
def remove_image():
    """删除本地镜像"""
    try:
        data = request.get_json()
        image_id = data.get('imageId')
        
        if not image_id:
            return error_response('缺少 imageId 参数', 400)
        
        service = get_docker_service()
        service.remove_image(image_id)
        
        return success_response(message='镜像删除成功')
    except Exception as e:
        logger.error(f"删除镜像失败: {str(e)}")
        return error_response(str(e), 500)
