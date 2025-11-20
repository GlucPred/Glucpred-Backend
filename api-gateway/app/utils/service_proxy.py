import requests
from flask import jsonify, request
from config.settings import Config


class ServiceProxy:
    """Proxy for forwarding requests to microservices"""
    
    @staticmethod
    def forward_request(service_url, path, flask_request=None, method=None, data=None, headers=None, params=None):
        """
        Forward request to a microservice
        
        Args:
            service_url (str): Base URL of the service
            path (str): Path to append to the URL
            flask_request: Flask request object (optional, extracts method/data/headers/params from it)
            method (str): HTTP method (overrides flask_request.method if both provided)
            data (dict): Request body (overrides flask_request data if both provided)
            headers (dict): Request headers (overrides flask_request headers if both provided)
            params (dict): Query parameters (overrides flask_request.args if both provided)
            
        Returns:
            tuple: (response_json, status_code)
        """
        # If flask_request is provided, extract method, data, headers from it
        if flask_request is not None:
            if method is None:
                method = flask_request.method
            if data is None:
                data = flask_request.get_json(silent=True) if flask_request.is_json else None
            if headers is None:
                # Copy headers from flask request, excluding Host
                headers = {key: value for key, value in flask_request.headers if key != 'Host'}
            if params is None and flask_request.args:
                params = dict(flask_request.args)
        
        # Default method
        if method is None:
            method = 'GET'
        
        url = f"{service_url}{path}"
        timeout = Config.REQUEST_TIMEOUT
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, params=params, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, params=params, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, headers=headers, timeout=timeout)
            else:
                return {'error': 'Método no soportado'}, 405
            
            return response.json(), response.status_code
            
        except requests.exceptions.ConnectionError:
            return {'error': 'Servicio no disponible'}, 503
        except requests.exceptions.Timeout:
            return {'error': 'Timeout al conectar con el servicio'}, 504
        except requests.exceptions.RequestException as e:
            return {'error': f'Error al conectar con el servicio: {str(e)}'}, 500
        except Exception as e:
            return {'error': f'Error al procesar la solicitud: {str(e)}'}, 500
