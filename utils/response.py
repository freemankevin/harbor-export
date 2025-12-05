from flask import jsonify

def success_response(data=None, message='Success', code=200):
    """成功响应"""
    response = {
        'success': True,
        'message': message,
        'code': code
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), code

def error_response(message='Error', code=400, details=None):
    """错误响应"""
    response = {
        'success': False,
        'message': message,
        'code': code
    }
    if details:
        response['details'] = details
    return jsonify(response), code
