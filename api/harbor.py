from flask import Blueprint, request
from services.harbor_service import HarborService
from utils.response import success_response, error_response
from utils.auth import require_harbor_config
from utils.logger import setup_logger

logger = setup_logger('api_harbor')

harbor_bp = Blueprint('harbor', __name__, url_prefix='/api/harbor')

@harbor_bp.route('/test-connection', methods=['POST'])
@require_harbor_config
def test_connection():
    """测试 Harbor 连接"""
    try:
        data = request.get_json()
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        if service.test_connection():
            projects = service.get_projects()
            return success_response(
                data={'projects': projects},
                message=f'连接成功，找到 {len(projects)} 个项目'
            )
        else:
            return error_response('连接失败，请检查配置', 401)
            
    except Exception as e:
        logger.error(f"测试连接失败: {str(e)}")
        return error_response(str(e), 500)

@harbor_bp.route('/projects', methods=['POST'])
@require_harbor_config
def get_projects():
    """获取项目列表"""
    try:
        data = request.get_json()
        page = data.get('page', 1)
        page_size = data.get('pageSize', 100)
        
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        projects = service.get_projects(page, page_size)
        return success_response(data={'projects': projects})
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        return error_response(str(e), 500)

@harbor_bp.route('/projects/<project_name>', methods=['POST'])
@require_harbor_config
def get_project_detail(project_name):
    """获取项目详情"""
    try:
        data = request.get_json()
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        detail = service.get_project_detail(project_name)
        return success_response(data={'project': detail})
        
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        return error_response(str(e), 500)

@harbor_bp.route('/repositories', methods=['POST'])
@require_harbor_config
def get_repositories():
    """获取仓库列表"""
    try:
        data = request.get_json()
        project = data.get('project')
        page = data.get('page', 1)
        page_size = data.get('pageSize', 100)
        
        if not project:
            return error_response('缺少 project 参数', 400)
        
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        repositories = service.get_repositories(project, page, page_size)
        
        # 获取每个仓库的 artifacts (tags)
        for repo in repositories:
            repo_name = repo['name'].split('/')[-1]
            artifacts = service.get_artifacts(project, repo_name)
            repo['artifacts'] = artifacts
            repo['tags'] = []
            for artifact in artifacts:
                repo['tags'].extend(artifact['tags'])
            repo['tags'] = list(set(repo['tags']))  # 去重
        
        return success_response(data={'repositories': repositories})
        
    except Exception as e:
        logger.error(f"获取仓库列表失败: {str(e)}")
        return error_response(str(e), 500)

@harbor_bp.route('/search', methods=['POST'])
@require_harbor_config
def search_repositories():
    """搜索仓库"""
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return error_response('缺少 query 参数', 400)
        
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        results = service.search_repositories(query)
        return success_response(data={'results': results})
        
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return error_response(str(e), 500)

@harbor_bp.route('/system-info', methods=['POST'])
@require_harbor_config
def get_system_info():
    """获取系统信息"""
    try:
        data = request.get_json()
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        info = service.get_system_info()
        return success_response(data={'info': info})
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return error_response(str(e), 500)

@harbor_bp.route('/statistics', methods=['POST'])
@require_harbor_config
def get_statistics():
    """获取统计信息"""
    try:
        data = request.get_json()
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        stats = service.get_statistics()
        return success_response(data={'statistics': stats})
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return error_response(str(e), 500)
