import requests
from flask import jsonify
from config.settings import Config


class ServiceProxy:
    """Proxy for forwarding requests to microservices"""
    
    @staticmethod
    def forward_request(service_url, path='', method='GET', data=None, headers=None):
        """
        Forward request to a microservice
        
        Args:
            service_url (str): Base URL of the service
            path (str): Path to append to the URL
            method (str): HTTP method
            data (dict): Request body
            headers (dict): Request headers
            
        Returns:
            tuple: (response_json, status_code)
        """
        url = f"{service_url}{path}"
        timeout = Config.REQUEST_TIMEOUT
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
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
