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
        
        return success_response(data={'repositories': repositories})
        
    except Exception as e:
        logger.error(f"获取仓库列表失败: {str(e)}")
        return error_response(str(e), 500)

@harbor_bp.route('/repository/tags', methods=['POST'])
@require_harbor_config
def get_repository_tags():
    """按选择获取指定仓库的标签列表"""
    try:
        data = request.get_json()
        project = data.get('project')
        repo_full_name = data.get('repo')
        if not project or not repo_full_name:
            return error_response('缺少参数', 400)
        service = HarborService(data['harborUrl'], data['username'], data['password'])
        logger.info(f"[tags] req project={project} repo={repo_full_name}")
        tags = []
        try:
            tags = service.get_registry_tags(repo_full_name)
        except Exception:
            tags = []
        if not tags:
            parts = repo_full_name.split('/')
            repo_path = '/'.join(parts[1:]) if len(parts) > 1 else parts[0]
            try:
                tags = service.get_registry_tags(repo_path)
            except Exception:
                tags = []
        artifacts_count = 0
        if not tags:
            # 先用完整仓库名取 artifacts
            try:
                artifacts = service.get_all_artifacts(project, repo_full_name)
                artifacts_count = len(artifacts)
                for a in artifacts:
                    tags.extend(a.get('tags', []))
            except Exception as e:
                if '404' in str(e):
                    artifacts = []
                else:
                    artifacts = []
            # 若仍为空，尝试去前缀仓库路径
            if not tags:
                try:
                    parts = repo_full_name.split('/')
                    repo_path = '/'.join(parts[1:]) if len(parts) > 1 else parts[0]
                    artifacts2 = service.get_all_artifacts(project, repo_path)
                    artifacts_count = max(artifacts_count, len(artifacts2))
                    for a in artifacts2:
                        tags.extend(a.get('tags', []))
                except Exception:
                    pass
            tags = list(set(tags))
        logger.info(f"[tags] artifacts={artifacts_count} tags={len(tags)}")
        return success_response(data={'tags': tags})
    except Exception as e:
        logger.error(f"获取仓库标签失败: {str(e)}")
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

@harbor_bp.route('/check-upload-permission', methods=['POST'])
@require_harbor_config
def check_upload_permission():
    """检查用户是否有上传镜像的权限"""
    try:
        data = request.get_json()
        project = data.get('project')
        
        if not project:
            return error_response('缺少 project 参数', 400)
        
        service = HarborService(
            data['harborUrl'],
            data['username'],
            data['password']
        )
        
        result = service.check_upload_permission(project)
        
        if result['has_permission']:
            return success_response(data=result, message=result['message'])
        else:
            return error_response(result['message'], 403)
        
    except Exception as e:
        logger.error(f"检查上传权限失败: {str(e)}")
        return error_response(str(e), 500)
