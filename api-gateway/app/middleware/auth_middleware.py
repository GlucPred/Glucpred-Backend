from flask import request
from functools import wraps


def extract_auth_header(f):
    """
    Decorator to extract authorization header from request
    and pass it to the service
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        headers = {}
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers.get('Authorization')
        return f(*args, headers=headers, **kwargs)
    return decorated
