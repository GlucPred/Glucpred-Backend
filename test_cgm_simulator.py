#!/usr/bin/env python3
"""
Script de prueba para simular un CGM (Continuous Glucose Monitor)
que envía mediciones de glucosa cada 5 minutos al backend.

Esto probará el flujo completo:
1. POST /api/records/ → Crear medición de glucosa
2. Records-service clasifica y publica evento Kafka
3. Alerts-service escucha Kafka y crea alerta si es necesario
4. GET /api/alerts/ → Verificar que se crearon las alertas

Uso:
    python test_cgm_simulator.py <JWT_TOKEN>
    
Ejemplo:
    python test_cgm_simulator.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
"""

import sys
import time
import requests
import json
from datetime import datetime
import random

# Configuración
API_BASE_URL = "http://localhost:5000/api"
INTERVAL_SECONDS = 5  # Simular lectura cada 5 segundos (en producción serían 5 minutos)

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def get_headers(token):
    """Genera los headers con el token JWT"""
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

def generate_glucose_reading(scenario='normal'):
    """
    Genera una lectura de glucosa según diferentes escenarios.
    
    Escenarios:
    - normal: 70-140 mg/dL (sin alerta)
    - high: 140-180 mg/dL (alerta advertencia)
    - critical_high: >180 mg/dL (alerta crítica)
    - low: 50-70 mg/dL (alerta advertencia)
    - critical_low: <50 mg/dL (alerta crítica)
    """
    scenarios = {
        'normal': (70, 140),
        'high': (140, 180),
        'critical_high': (180, 250),
        'low': (50, 70),
        'critical_low': (30, 50)
    }
    
    min_val, max_val = scenarios.get(scenario, (70, 140))
    return round(random.uniform(min_val, max_val), 1)

def create_glucose_record(token, glucose_value):
    """Crea un registro de glucosa"""
    url = f"{API_BASE_URL}/records/"
    
    data = {
        "glucose_value": glucose_value,
        "measurement_time": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        response = requests.post(url, json=data, headers=get_headers(token))
        
        if response.status_code == 201:
            result = response.json()
            record = result.get('record', {})
            classification = record.get('classification', 'unknown')
            record_id = record.get('id', 'N/A')
            
            # Color según clasificación
            if classification == 'critico':
                color = Colors.FAIL
                emoji = "🔴"
            elif classification == 'alto':
                color = Colors.WARNING
                emoji = "🟡"
            elif classification == 'bajo':
                color = Colors.WARNING
                emoji = "🟠"
            else:
                color = Colors.OKGREEN
                emoji = "🟢"
            
            print(f"{color}{emoji} Medición registrada: {glucose_value} mg/dL - Clasificación: {classification.upper()} (ID: {record_id}){Colors.ENDC}")
            return record
        else:
            print_error(f"Error al registrar medición: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Excepción al crear registro: {e}")
        return None

def get_alerts(token, alert_type='todas'):
    """Obtiene las alertas del usuario"""
    url = f"{API_BASE_URL}/alerts/?type={alert_type}&limit=10"
    
    try:
        response = requests.get(url, headers=get_headers(token))
        
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Error al obtener alertas: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Excepción al obtener alertas: {e}")
        return None

def get_unread_count(token):
    """Obtiene el contador de alertas no leídas"""
    url = f"{API_BASE_URL}/alerts/unread-count"
    
    try:
        response = requests.get(url, headers=get_headers(token))
        
        if response.status_code == 200:
            return response.json().get('unread_count', 0)
        else:
            return 0
            
    except Exception as e:
        return 0

def display_alerts(alerts_data):
    """Muestra las alertas en formato legible"""
    if not alerts_data or 'alerts' not in alerts_data:
        print_warning("No hay alertas disponibles")
        return
    
    alerts = alerts_data['alerts']
    total = alerts_data.get('total', 0)
    
    print(f"\n{Colors.BOLD}📋 Alertas encontradas: {total}{Colors.ENDC}")
    print("─" * 60)
    
    for alert in alerts:
        alert_id = alert.get('id')
        title = alert.get('title')
        message = alert.get('message')
        severity = alert.get('severity')
        glucose_value = alert.get('glucose_value')
        created_at = alert.get('created_at')
        is_read = alert.get('is_read')
        
        # Color según severidad
        if severity == 'critico':
            color = Colors.FAIL
            badge = "🔴 CRÍTICO"
        elif severity == 'advertencia':
            color = Colors.WARNING
            badge = "🟡 ADVERTENCIA"
        else:
            color = Colors.OKBLUE
            badge = "🔵 INFO"
        
        read_status = "✓ Leída" if is_read else "● No leída"
        
        print(f"{color}[{alert_id}] {badge}{Colors.ENDC}")
        print(f"  Título: {title}")
        print(f"  Mensaje: {message}")
        if glucose_value:
            print(f"  Glucosa: {glucose_value} mg/dL")
        print(f"  Fecha: {created_at}")
        print(f"  Estado: {read_status}")
        print("─" * 60)

def run_test_scenarios(token):
    """Ejecuta diferentes escenarios de prueba"""
    
    print_header("SIMULADOR DE CGM - GLUCPRED")
    print_info("Iniciando simulación de mediciones de glucosa...")
    print_info(f"Intervalo: {INTERVAL_SECONDS} segundos entre mediciones\n")
    
    # Escenarios de prueba
    test_cases = [
        ('normal', 'Nivel normal (70-140 mg/dL)'),
        ('normal', 'Nivel normal (70-140 mg/dL)'),
        ('high', 'Nivel alto (140-180 mg/dL) - Debería generar alerta ADVERTENCIA'),
        ('normal', 'Nivel normal (70-140 mg/dL)'),
        ('critical_high', 'Nivel crítico alto (>180 mg/dL) - Debería generar alerta CRÍTICA'),
        ('normal', 'Nivel normal (70-140 mg/dL)'),
        ('low', 'Nivel bajo (50-70 mg/dL) - Debería generar alerta ADVERTENCIA'),
        ('normal', 'Nivel normal (70-140 mg/dL)'),
        ('critical_low', 'Nivel crítico bajo (<50 mg/dL) - Debería generar alerta CRÍTICA'),
        ('normal', 'Nivel normal (70-140 mg/dL)'),
    ]
    
    print(f"{Colors.BOLD}Escenarios de prueba planificados:{Colors.ENDC}")
    for i, (scenario, description) in enumerate(test_cases, 1):
        print(f"  {i}. {description}")
    
    print(f"\n{Colors.OKCYAN}Comenzando tests...{Colors.ENDC}\n")
    
    measurement_count = 0
    
    for scenario, description in test_cases:
        measurement_count += 1
        
        print(f"\n{Colors.BOLD}━━━ Medición #{measurement_count} ━━━{Colors.ENDC}")
        print(f"Escenario: {description}")
        
        # Generar y enviar medición
        glucose_value = generate_glucose_reading(scenario)
        record = create_glucose_record(token, glucose_value)
        
        if record:
            # Esperar un poco para que Kafka procese
            print_info("Esperando procesamiento de Kafka...")
            time.sleep(2)
            
            # Verificar alertas no leídas
            unread_count = get_unread_count(token)
            if unread_count > 0:
                print_warning(f"Tienes {unread_count} alerta(s) no leída(s)")
        
        # Esperar intervalo antes de siguiente medición
        if measurement_count < len(test_cases):
            print(f"\n{Colors.OKCYAN}⏳ Esperando {INTERVAL_SECONDS} segundos para siguiente medición...{Colors.ENDC}")
            time.sleep(INTERVAL_SECONDS)
    
    # Resumen final
    print_header("RESUMEN DE PRUEBAS")
    print_success(f"Total de mediciones enviadas: {measurement_count}")
    
    # Obtener y mostrar todas las alertas
    print_info("Obteniendo alertas generadas...")
    alerts_data = get_alerts(token, 'critica')
    
    if alerts_data:
        display_alerts(alerts_data)
    
    # Mostrar contador de alertas no leídas
    unread_count = get_unread_count(token)
    print(f"\n{Colors.BOLD}📊 Total de alertas no leídas: {unread_count}{Colors.ENDC}")

def run_continuous_mode(token):
    """Modo continuo: simula CGM real enviando mediciones indefinidamente"""
    
    print_header("MODO CONTINUO - SIMULADOR CGM")
    print_warning("Este modo enviará mediciones cada 5 segundos indefinidamente")
    print_info("Presiona Ctrl+C para detener\n")
    
    measurement_count = 0
    
    try:
        while True:
            measurement_count += 1
            
            # Generar escenario aleatorio con mayor probabilidad de normal
            rand = random.random()
            if rand < 0.6:  # 60% normal
                scenario = 'normal'
            elif rand < 0.75:  # 15% alto
                scenario = 'high'
            elif rand < 0.85:  # 10% crítico alto
                scenario = 'critical_high'
            elif rand < 0.95:  # 10% bajo
                scenario = 'low'
            else:  # 5% crítico bajo
                scenario = 'critical_low'
            
            print(f"\n{Colors.BOLD}━━━ Medición #{measurement_count} - {datetime.now().strftime('%H:%M:%S')} ━━━{Colors.ENDC}")
            
            glucose_value = generate_glucose_reading(scenario)
            record = create_glucose_record(token, glucose_value)
            
            if record:
                # Verificar alertas cada 5 mediciones
                if measurement_count % 5 == 0:
                    unread_count = get_unread_count(token)
                    if unread_count > 0:
                        print_warning(f"📬 Tienes {unread_count} alerta(s) no leída(s)")
            
            time.sleep(INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print_header("SIMULACIÓN DETENIDA")
        print_success(f"Total de mediciones enviadas: {measurement_count}")
        
        # Mostrar alertas finales
        print_info("Obteniendo alertas generadas...")
        alerts_data = get_alerts(token, 'todas')
        if alerts_data:
            display_alerts(alerts_data)

def main():
    if len(sys.argv) < 2:
        print_error("Uso: python test_cgm_simulator.py <JWT_TOKEN>")
        print_info("\nEjemplo:")
        print(f"  python test_cgm_simulator.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        sys.exit(1)
    
    token = sys.argv[1]
    
    # Verificar conectividad
    print_info("Verificando conectividad con el backend...")
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health")
        if response.status_code == 200:
            print_success("✓ Backend conectado correctamente")
        else:
            print_error("✗ Backend no responde correctamente")
            sys.exit(1)
    except Exception as e:
        print_error(f"✗ No se puede conectar al backend: {e}")
        sys.exit(1)
    
    # Menú de opciones
    print(f"\n{Colors.BOLD}Selecciona modo de prueba:{Colors.ENDC}")
    print("1. Escenarios de prueba predefinidos (10 mediciones)")
    print("2. Modo continuo (mediciones infinitas cada 5 segundos)")
    
    choice = input(f"\n{Colors.OKCYAN}Opción [1/2]: {Colors.ENDC}").strip()
    
    if choice == '2':
        run_continuous_mode(token)
    else:
        run_test_scenarios(token)
    
    print(f"\n{Colors.OKGREEN}✓ Pruebas completadas{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
