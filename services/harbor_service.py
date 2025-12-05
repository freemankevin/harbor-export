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
        self.harbor_url = harbor_url.rstrip('/')
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
        project = self._request('GET', f'/projects/{project_name}')
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
        params = {'page': page, 'page_size': page_size}
        repos = self._request('GET', f'/projects/{project_name}/repositories', params=params)
        
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
        """获取 artifacts 列表"""
        # URL 编码仓库名
        encoded_repo = quote(repo_name, safe='')
        params = {'page': page, 'page_size': page_size, 'with_tag': True}
        
        artifacts = self._request(
            'GET',
            f'/projects/{project_name}/repositories/{encoded_repo}/artifacts',
            params=params
        )
        
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
