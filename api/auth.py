from flask import Blueprint, request, session
from utils.response import success_response, error_response
from utils.logger import setup_logger

logger = setup_logger('api_auth')

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u = data.get('username')
    p = data.get('password')
    if u == 'admin' and p == '123456':
        session['user'] = {'username': u}
        logger.info('用户登录成功')
        return success_response(data={'user': {'username': u}})
    return error_response('用户名或密码错误', 401)

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return success_response(message='已注销')

@auth_bp.route('/me', methods=['GET'])
def me():
    user = session.get('user')
    if not user:
        return error_response('未登录', 401)
    return success_response(data={'user': user})

