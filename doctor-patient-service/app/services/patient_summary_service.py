import requests
from app.services import DoctorPatientService
from config.settings import Config
import logging
import os

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', 'glucpred-internal-key-change-in-production')


class PatientSummaryService:
    """
    Servicio para obtener resumen completo de pacientes con datos de otros microservicios
    """
    
    # URLs de otros microservicios
    PROFILE_SERVICE_URL = 'http://profile-service:8082'
    RECORDS_SERVICE_URL = 'http://records-service:8085'
    ALERTS_SERVICE_URL = 'http://alerts-service:8086'
    AUTH_SERVICE_URL = 'http://authentication-service:8081'
    
    @staticmethod
    def get_patients_summary(doctor_user_id, auth_token):
        """
        Obtiene resumen de todos los pacientes del doctor con:
        - Información del perfil
        - Última medición de glucosa
        - Estado actual (basado en alertas)
        - Cantidad de alertas
        
        Args:
            doctor_user_id (int): ID del doctor
            auth_token (str): Token JWT para autenticación en otros servicios
            
        Returns:
            tuple: (patients_summary_list, error_message)
        """
        try:
            # Obtener pacientes activos del doctor
            relations, error = DoctorPatientService.get_doctor_patients(
                doctor_user_id=doctor_user_id,
                estado='A'
            )
            
            if error:
                return None, error
            
            if not relations:
                return [], None
            
            patients_summary = []
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'X-Internal-Api-Key': INTERNAL_API_KEY
            }
            
            # Obtener todos los usuarios y perfiles de una vez
            try:
                auth_response = requests.get(
                    f'{PatientSummaryService.AUTH_SERVICE_URL}/api/auth/users',
                    headers=headers,
                    timeout=5
                )
                users_map = {u['id']: u for u in auth_response.json().get('users', [])} if auth_response.status_code == 200 else {}
            except Exception as e:
                logger.error(f"Error getting users: {e}")
                users_map = {}
            
            try:
                profile_response = requests.get(
                    f'{PatientSummaryService.PROFILE_SERVICE_URL}/api/profile/all',
                    headers=headers,
                    timeout=5
                )
                profiles_map = {p['user_id']: p for p in profile_response.json().get('profiles', [])} if profile_response.status_code == 200 else {}
            except Exception as e:
                logger.error(f"Error getting profiles: {e}")
                profiles_map = {}
            
            for relation in relations:
                patient_user_id = relation['patient_user_id']
                
                # Obtener datos del usuario y perfil
                user_data = users_map.get(patient_user_id, {})
                profile_data = profiles_map.get(patient_user_id, {})
                
                # Construir resumen del paciente
                patient_data = {
                    'patient_user_id': patient_user_id,
                    'nombre_completo': user_data.get('nombre_completo'),
                    'edad': profile_data.get('edad'),
                    'ultima_glucosa': None,
                    'estado': 'Desconocido',
                    'alertas_count': 0,
                    'fecha_asignacion': relation['fecha_asignacion']
                }
                
                # 2. Obtener última glucosa
                try:
                    records_response = requests.get(
                        f'{PatientSummaryService.RECORDS_SERVICE_URL}/api/records/user/{patient_user_id}/latest',
                        headers=headers,
                        timeout=3
                    )
                    
                    if records_response.status_code == 200:
                        latest_record = records_response.json()
                        patient_data['ultima_glucosa'] = latest_record.get('glucose_value')
                        patient_data['ultima_medicion_fecha'] = latest_record.get('measurement_time')
                except Exception as e:
                    logger.warning(f"Error getting latest glucose for patient {patient_user_id}: {e}")
                
                # 3. Obtener alertas críticas recientes (últimas 24 horas)
                try:
                    alerts_response = requests.get(
                        f'{PatientSummaryService.ALERTS_SERVICE_URL}/api/alerts/patient/{patient_user_id}/critical-count',
                        headers=headers,
                        params={'hours': 24},
                        timeout=3
                    )
                    
                    if alerts_response.status_code == 200:
                        alerts_data = alerts_response.json()
                        patient_data['alertas_count'] = alerts_data.get('critical_count', 0)
                except Exception as e:
                    logger.warning(f"Error getting alerts for patient {patient_user_id}: {e}")
                
                # 4. Determinar estado basado en alertas críticas
                if patient_data['alertas_count'] >= 3:
                    patient_data['estado'] = 'Critica'
                elif patient_data['alertas_count'] >= 1:
                    patient_data['estado'] = 'Moderada'
                else:
                    patient_data['estado'] = 'Estable'
                
                patients_summary.append(patient_data)
            
            # Ordenar por estado (Critica primero) y luego por alertas
            estado_order = {'Critica': 0, 'Moderada': 1, 'Estable': 2, 'Desconocido': 3}
            patients_summary.sort(
                key=lambda p: (estado_order.get(p['estado'], 999), -p['alertas_count'])
            )
            
            return patients_summary, None
            
        except Exception as e:
            logger.error(f"Error getting patients summary: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def get_patient_detail(patient_user_id, doctor_user_id, auth_token, period='day'):
        """
        Obtiene detalle completo de un paciente para la vista de doctor:
        - Perfil completo
        - Estadísticas de glucosa (promedio, % en rango)
        - Tendencia de glucosa (gráfica)
        - Última observación médica
        
        Args:
            patient_user_id (int): ID del paciente
            doctor_user_id (int): ID del doctor
            auth_token (str): Token JWT
            period (str): 'day', 'week', 'month'
            
        Returns:
            tuple: (patient_detail_dict, error_message)
        """
        try:
            # Verificar que el doctor tenga acceso a este paciente
            relations, error = DoctorPatientService.get_doctor_patients(
                doctor_user_id=doctor_user_id,
                estado='A'
            )
            
            if error:
                return None, error
            
            patient_ids = [r['patient_user_id'] for r in relations]
            if patient_user_id not in patient_ids:
                return None, 'No tienes acceso a este paciente'
            
            headers = {'Authorization': f'Bearer {auth_token}'}
            patient_detail = {
                'patient_user_id': patient_user_id,
                'profile': {},
                'glucose_stats': {},
                'glucose_trend': [],
                'latest_observation': None
            }
            
            # 1. Obtener perfil completo
            try:
                profile_response = requests.get(
                    f'{PatientSummaryService.PROFILE_SERVICE_URL}/api/profile/{patient_user_id}',
                    headers=headers,
                    timeout=3
                )
                
                if profile_response.status_code == 200:
                    patient_detail['profile'] = profile_response.json()
            except Exception as e:
                logger.warning(f"Error getting profile: {e}")
            
            # 2. Obtener estadísticas de glucosa
            try:
                stats_response = requests.get(
                    f'{PatientSummaryService.RECORDS_SERVICE_URL}/api/records/user/{patient_user_id}/statistics',
                    headers=headers,
                    params={'period': period},
                    timeout=3
                )
                
                if stats_response.status_code == 200:
                    patient_detail['glucose_stats'] = stats_response.json()
            except Exception as e:
                logger.warning(f"Error getting glucose stats: {e}")
            
            # 3. Obtener tendencia de glucosa
            try:
                trend_response = requests.get(
                    f'{PatientSummaryService.RECORDS_SERVICE_URL}/api/records/user/{patient_user_id}/history',
                    headers=headers,
                    params={'limit': 50, 'period': period},
                    timeout=3
                )
                
                if trend_response.status_code == 200:
                    records = trend_response.json().get('records', [])
                    patient_detail['glucose_trend'] = records
            except Exception as e:
                logger.warning(f"Error getting glucose trend: {e}")
            
            # 4. Obtener última observación médica (de este doctor)
            from app.services import MedicalObservationService
            observations, total, error = MedicalObservationService.get_patient_observations(
                patient_user_id=patient_user_id,
                doctor_user_id=doctor_user_id,
                limit=1
            )
            
            if observations and len(observations) > 0:
                patient_detail['latest_observation'] = observations[0]
            
            return patient_detail, None
            
        except Exception as e:
            logger.error(f"Error getting patient detail: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def get_available_patients(auth_token):
        """
        Obtiene lista de pacientes disponibles (sin médico asignado) con su información completa.
        Este endpoint se usa para que un médico pueda ver y seleccionar pacientes disponibles.
        
        Args:
            auth_token (str): Token JWT para autenticación en otros servicios
            
        Returns:
            tuple: (available_patients_list, error_message)
        """
        try:
            from app.models import DoctorPatientRelation
            from app.extensions import db
            
            # Obtener todos los patient_user_id que tienen médico activo
            patients_with_doctor = db.session.query(
                DoctorPatientRelation.patient_user_id
            ).filter(
                DoctorPatientRelation.estado == 'A'
            ).all()
            
            assigned_patient_ids = [p[0] for p in patients_with_doctor]
            
            # Obtener TODOS los perfiles del profile-service
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'X-Internal-Api-Key': INTERNAL_API_KEY
            }
            
            try:
                profile_response = requests.get(
                    f'{PatientSummaryService.PROFILE_SERVICE_URL}/api/profile/all',
                    headers=headers,
                    timeout=5
                )
                
                if profile_response.status_code != 200:
                    logger.warning(f"Profile service returned status {profile_response.status_code}")
                    all_profiles = []
                else:
                    all_profiles = profile_response.json().get('profiles', [])
                    logger.info(f"Profile service returned {len(all_profiles)} profiles")
            except Exception as e:
                logger.error(f"Error calling profile service: {e}")
                all_profiles = []
            
            # Obtener información de usuarios del authentication-service para filtrar por rol
            try:
                # Llamar al authentication-service para obtener usuarios
                auth_response = requests.get(
                    f'{PatientSummaryService.AUTH_SERVICE_URL}/api/auth/users',
                    headers=headers,
                    timeout=5
                )
                
                if auth_response.status_code == 200:
                    all_users = auth_response.json().get('users', [])
                    logger.info(f"Auth service returned {len(all_users)} users")
                    # Crear mapa user_id -> user_data solo para pacientes
                    patient_users = {
                        u['id']: u for u in all_users 
                        if u.get('rol') == 'Paciente'
                    }
                    logger.info(f"Found {len(patient_users)} patients in auth service")
                else:
                    logger.warning(f"Auth service returned status {auth_response.status_code}")
                    patient_users = {}
            except Exception as e:
                logger.error(f"Error calling auth service: {e}")
                patient_users = {}
            
            # Filtrar solo pacientes SIN médico asignado
            available_patients = []
            
            logger.info(f"Processing {len(all_profiles)} profiles, {len(assigned_patient_ids)} assigned patients")
            
            for profile in all_profiles:
                user_id = profile.get('user_id')
                
                # Skip si NO es paciente (no está en patient_users)
                if user_id not in patient_users:
                    continue
                
                # Skip si tiene médico asignado
                if user_id in assigned_patient_ids:
                    continue
                
                # Obtener datos del usuario
                user_data = patient_users.get(user_id, {})
                
                # Construir datos del paciente disponible
                patient_data = {
                    'patient_user_id': user_id,
                    'nombre_completo': user_data.get('nombre_completo', 'Desconocido'),
                    'edad': profile.get('edad'),
                    'peso': profile.get('peso'),
                    'altura': profile.get('altura'),
                    'genero': user_data.get('genero', profile.get('genero')),  # Priorizar del auth-service
                    'medicamentos': profile.get('medicamentos'),
                    'antecedentes': profile.get('antecedentes'),
                    'fecha_diagnostico': profile.get('fecha_diagnostico'),
                    'ultima_glucosa': None,
                    'alertas_count': 0
                }
                
                # Obtener última glucosa del paciente
                try:
                    records_response = requests.get(
                        f'{PatientSummaryService.RECORDS_SERVICE_URL}/api/records/user/{user_id}/latest',
                        headers=headers,
                        timeout=3
                    )
                    
                    if records_response.status_code == 200:
                        latest_record = records_response.json()
                        patient_data['ultima_glucosa'] = latest_record.get('glucose_value')
                        patient_data['ultima_medicion_fecha'] = latest_record.get('measurement_time')
                except Exception as e:
                    logger.warning(f"Error getting glucose for patient {user_id}: {e}")
                
                # Obtener cantidad de alertas críticas (últimas 24h)
                try:
                    alerts_response = requests.get(
                        f'{PatientSummaryService.ALERTS_SERVICE_URL}/api/alerts/critical-count',
                        headers={**headers, 'X-User-ID': str(user_id)},
                        params={'hours': 24},
                        timeout=3
                    )
                    
                    if alerts_response.status_code == 200:
                        alerts_data = alerts_response.json()
                        patient_data['alertas_count'] = alerts_data.get('critical_count', 0)
                except Exception as e:
                    logger.warning(f"Error getting alerts for patient {user_id}: {e}")
                
                available_patients.append(patient_data)
            
            # Ordenar por nombre
            available_patients.sort(key=lambda p: p.get('nombre_completo', ''))
            
            return available_patients, None
            
        except Exception as e:
            logger.error(f"Error getting available patients: {e}", exc_info=True)
            return None, 'Error interno del servidor'
