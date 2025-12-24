import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse, quote
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from config import Config
from utils.auth import get_auth_header
from utils.logger import setup_logger

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = setup_logger('harbor_service')

class HarborService:
    """Harbor 服务类"""
    
    def __init__(self, harbor_url, username, password):
        # 允许传入不带协议的地址，默认 https
        url = (harbor_url or '').strip()
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        self.harbor_url = url.rstrip('/')
        self.username = username
        self.password = password
        self.headers = get_auth_header(username, password)
        self.api_base = f"{self.harbor_url}/api/{Config.HARBOR_API_VERSION}"
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "POST"])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _request(self, method, endpoint, **kwargs):
        """统一请求方法"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        kwargs.setdefault('headers', {}).update(self.headers)
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', Config.HARBOR_REQUEST_TIMEOUT)
        
        try:
            logger.info(f"{method.upper()} {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Harbor API 错误: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            raise Exception(f"网络请求失败: {str(e)}")
    
    def test_connection(self):
        """测试连接"""
        try:
            self._request('GET', '/systeminfo')
            return True
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            return False
    
    def get_projects(self, page=1, page_size=100):
        """获取项目列表"""
        params = {'page': page, 'page_size': page_size}
        projects = self._request('GET', '/projects', params=params)
        
        return [{
            'project_id': p.get('project_id'),
            'name': p.get('name'),
            'public': p.get('metadata', {}).get('public') == 'true',
            'repo_count': p.get('repo_count', 0),
            'created': p.get('creation_time'),
            'updated': p.get('update_time')
        } for p in projects]
    
    def get_project_detail(self, project_name):
        """获取项目详情"""
        from urllib.parse import quote
        encoded_project = quote(project_name, safe='')
        project = self._request('GET', f'/projects/{encoded_project}')
        return {
            'project_id': project.get('project_id'),
            'name': project.get('name'),
            'owner': project.get('owner_name'),
            'public': project.get('metadata', {}).get('public') == 'true',
            'repo_count': project.get('repo_count', 0),
            'storage_limit': project.get('storage_limit', -1),
            'created': project.get('creation_time'),
            'updated': project.get('update_time')
        }
    
    def get_repositories(self, project_name, page=1, page_size=100):
        """获取仓库列表"""
        from urllib.parse import quote
        params = {'page': page, 'page_size': page_size}
        encoded_project = quote(project_name, safe='')
        try:
            repos = self._request('GET', f'/projects/{encoded_project}/repositories', params=params)
        except Exception as e:
            if '404' in str(e):
                # 某些环境需要使用 project_id
                detail = self.get_project_detail(project_name)
                pid = detail.get('project_id')
                repos = self._request('GET', f'/projects/{pid}/repositories', params=params)
            else:
                raise
        return [{
            'id': r.get('id'),
            'name': r.get('name'),
            'project_name': project_name,
            'artifact_count': r.get('artifact_count', 0),
            'pull_count': r.get('pull_count', 0),
            'created': r.get('creation_time'),
            'updated': r.get('update_time')
        } for r in repos]
    
    def get_artifacts(self, project_name, repo_name, page=1, page_size=100):
        params = {'page': page, 'page_size': page_size, 'with_tag': 'true'}
        encoded_project = quote(project_name, safe='')
        encoded_repo = quote(repo_name, safe='/')
        # 1) 优先使用项目名 + 完整仓库路径
        try:
            artifacts = self._request('GET', f'/projects/{encoded_project}/repositories/{encoded_repo}/artifacts', params=params)
        except Exception as e1:
            artifacts = []
            if '404' in str(e1):
                # 2) 404 时尝试去除项目名前缀的仓库路径
                parts = repo_name.split('/')
                stripped = '/'.join(parts[1:]) if len(parts) > 1 else parts[0]
                encoded_alt_repo = quote(stripped, safe='/')
                try:
                    artifacts = self._request('GET', f'/projects/{encoded_project}/repositories/{encoded_alt_repo}/artifacts', params=params)
                except Exception as e2:
                    artifacts = []
        # 若依然为空，先尝试完整仓库路径不编码（兼容部分部署）
        if not artifacts:
            try:
                artifacts = self._request('GET', f'/projects/{encoded_project}/repositories/{repo_name}/artifacts', params=params)
            except Exception:
                pass
        # 若仍为空，再尝试去项目前缀的仓库路径不编码
        if not artifacts:
            parts = repo_name.split('/')
            stripped = '/'.join(parts[1:]) if len(parts) > 1 else parts[0]
            try:
                artifacts = self._request('GET', f'/projects/{encoded_project}/repositories/{stripped}/artifacts', params=params)
            except Exception:
                pass
        # 若到此仍为空，尝试使用 project_id 路径（完整和去前缀）
        if not artifacts:
            detail = self.get_project_detail(project_name)
            pid = detail.get('project_id')
            try:
                artifacts = self._request('GET', f'/projects/{pid}/repositories/{encoded_repo}/artifacts', params=params)
            except Exception as e3:
                artifacts = []
            if not artifacts:
                parts = repo_name.split('/')
                stripped = '/'.join(parts[1:]) if len(parts) > 1 else parts[0]
                encoded_alt_repo = quote(stripped, safe='/')
                try:
                    artifacts = self._request('GET', f'/projects/{pid}/repositories/{encoded_alt_repo}/artifacts', params=params)
                except Exception:
                    artifacts = []

        result = []
        for artifact in artifacts:
            tags = [tag['name'] for tag in artifact.get('tags', [])] or ['<none>']
            result.append({
                'digest': artifact.get('digest'),
                'tags': tags,
                'size': artifact.get('size', 0),
                'push_time': artifact.get('push_time'),
                'pull_time': artifact.get('pull_time')
            })
        
        return result

    def get_all_artifacts(self, project_name, repo_name, page_size=100):
        """分页获取所有 artifacts 并聚合标签"""
        page = 1
        all_items = []
        while True:
            items = self.get_artifacts(project_name, repo_name, page=page, page_size=page_size)
            if not items:
                break
            all_items.extend(items)
            if len(items) < page_size:
                break
            page += 1
        return all_items
    
    def search_repositories(self, query, page=1, page_size=50):
        """搜索仓库"""
        params = {'q': query, 'page': page, 'page_size': page_size}
        results = self._request('GET', '/search', params=params)
        
        repositories = []
        if results and 'repository' in results:
            for repo in results['repository']:
                repositories.append({
                    'name': repo.get('repository_name'),
                    'project_name': repo.get('project_name'),
                    'public': repo.get('project_public', False)
                })
        
        return repositories
    
    def get_system_info(self):
        """获取系统信息"""
        info = self._request('GET', '/systeminfo')
        return {
            'harbor_version': info.get('harbor_version'),
            'registry_url': info.get('registry_url'),
            'external_url': info.get('external_url'),
            'auth_mode': info.get('auth_mode'),
            'project_creation_restriction': info.get('project_creation_restriction')
        }
    
    def get_registry_tags(self, repo_name):
        """直接通过 Registry v2 接口获取 tags 列表，作为 API 失败时的回退"""
        url = f"{self.harbor_url}/v2/{repo_name}/tags/list"
        try:
            logger.info(f"GET {url}")
            resp = self.session.get(url, headers=self.headers, verify=False, timeout=Config.HARBOR_REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json() or {}
            tags = data.get('tags') or []
            return tags
        except requests.exceptions.HTTPError as e:
            logger.error(f"Registry HTTP Error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Harbor Registry 错误: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Registry Request Error: {str(e)}")
            raise Exception(f"网络请求失败: {str(e)}")
    
    def get_statistics(self):
        """获取统计信息"""
        stats = self._request('GET', '/statistics')
        return {
            'total_project_count': stats.get('total_project_count', 0),
            'public_project_count': stats.get('public_project_count', 0),
            'private_project_count': stats.get('private_project_count', 0),
            'total_repo_count': stats.get('total_repo_count', 0),
            'total_storage_consumption': stats.get('total_storage_consumption', 0)
        }
    
    def check_upload_permission(self, project_name):
        """检查用户是否有上传镜像的权限"""
        try:
            encoded_project = quote(project_name, safe='')
            project = self._request('GET', f'/projects/{encoded_project}')
            
            current_user_url = f"{self.api_base}/users/current"
            try:
                response = self.session.get(
                    current_user_url,
                    headers=self.headers,
                    verify=False,
                    timeout=Config.HARBOR_REQUEST_TIMEOUT
                )
                response.raise_for_status()
                current_user = response.json()
                username = current_user.get('username')
            except Exception as e:
                logger.warning(f"无法获取当前用户信息: {str(e)}")
                username = self.username
            
            members_url = f'/projects/{encoded_project}/members'
            try:
                members = self._request('GET', members_url)
            except Exception as e:
                if '404' in str(e):
                    pid = project.get('project_id')
                    members = self._request('GET', f'/projects/{pid}/members')
                else:
                    raise
            
            user_role = None
            for member in members:
                member_name = member.get('entity_name')
                if member_name == username:
                    user_role = member.get('role_id')
                    break
            
            if user_role is None:
                is_public = project.get('metadata', {}).get('public') == 'true'
                if not is_public:
                    return {
                        'has_permission': False,
                        'message': f'您不是项目 {project_name} 的成员，无法上传镜像'
                    }
                else:
                    return {
                        'has_permission': False,
                        'message': f'您不是项目 {project_name} 的成员，公开项目也需要成员权限才能上传镜像'
                    }
            
            if user_role in [1, 2, 3]:
                return {
                    'has_permission': True,
                    'message': '您有权限上传镜像到此项目',
                    'role_id': user_role
                }
            else:
                return {
                    'has_permission': False,
                    'message': f'您的角色权限不足，无法上传镜像到项目 {project_name}'
                }
                
        except Exception as e:
            logger.error(f"检查上传权限失败: {str(e)}")
            raise Exception(f"检查上传权限失败: {str(e)}")
