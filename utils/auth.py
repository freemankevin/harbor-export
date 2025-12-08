import base64
from functools import wraps
from flask import request
from utils.response import error_response
from urllib.parse import urlparse

def get_auth_header(username, password):
    """生成 Basic Auth 头"""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def require_harbor_config(f):
    """装饰器：要求请求包含 Harbor 配置"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        if not data:
            return error_response('请求体不能为空', 400)
        
        required_fields = ['harborUrl', 'username', 'password']
        missing_fields = [f for f in required_fields if not data.get(f)]
        
        if missing_fields:
            return error_response(
                f'缺少必要字段: {", ".join(missing_fields)}',
                400
            )
        url = str(data.get('harborUrl')).strip()
        if url.lower() == 'string':
            return error_response('harborUrl 不能为示例值，请填写真实地址', 400)
        parsed = urlparse(url if url.startswith('http') else 'https://' + url)
        if not parsed.scheme or not parsed.netloc:
            return error_response('harborUrl 格式错误，请使用形如 https://host 的地址', 400)
        
        return f(*args, **kwargs)
    return decorated_function
