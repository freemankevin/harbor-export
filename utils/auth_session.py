from functools import wraps
from flask import request, session
from utils.response import error_response

def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            return error_response('未登录', 401)
        return f(*args, **kwargs)
    return wrapper

