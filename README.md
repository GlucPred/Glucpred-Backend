# Glucpred Backend - Microservices Architecture

Sistema de backend para la aplicación Glucpred basado en arquitectura de microservicios con Flask, SQLAlchemy y MySQL.

## 🏗️ Arquitectura

El sistema está compuesto por los siguientes servicios:

- **API Gateway** (Puerto 5000): Punto de entrada único que enruta las peticiones a los microservicios
- **Authentication Service** (Puerto 8081): Manejo de registro y autenticación de usuarios con JWT
- **Profile Service** (Puerto 8082): Gestión de perfiles de pacientes

Cada servicio tiene su propia base de datos MySQL y se ejecuta en un contenedor Docker independiente.

## 📋 Requisitos

- Docker
- Docker Compose

## 🚀 Ejecución con Docker

```bash
cd api-gateway
docker-compose up --build
```

**Servicios levantados:**
- API Gateway con Swagger: http://localhost:5000
- Documentación Swagger: http://localhost:5000/docs
- Authentication Service: http://localhost:8081
- Profile Service: http://localhost:8082
- MySQL Auth DB: localhost:3307
- MySQL Profile DB: localhost:3308

**Comandos útiles:**
```bash
# Ver logs
docker-compose logs -f [servicio]

# Detener servicios
docker-compose down

# Detener y eliminar datos
docker-compose down -v
```

### Desarrollo Local (Sin Docker)

#### 1. Authentication Service

```bash
cd authentication-service
pip install -r requirements.txt
python run.py
```

El servicio estará disponible en `http://localhost:8081`

#### 2. Profile Service

```bash
cd profile-service
pip install -r requirements.txt
python run.py
```

El servicio estará disponible en `http://localhost:8082`

#### 3. API Gateway

```bash
cd api-gateway
pip install -r requirements.txt
python run.py
```

El gateway estará disponible en `http://localhost:5000`

> **Nota:** Para ejecutar los servicios individualmente, necesitarás tener MySQL instalado y configurar las bases de datos manualmente. Se recomienda usar Docker Compose.

## 📂 Estructura del Proyecto

Cada microservicio sigue una arquitectura por capas profesional:

### Authentication Service
```
authentication-service/
├── app/
│   ├── __init__.py          # Factory pattern
│   ├── extensions.py        # SQLAlchemy initialization
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # User model
│   ├── routes/
│   │   ├── __init__.py
│   │   └── auth_routes.py   # Authentication endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py  # Business logic
│   └── utils/
│       ├── __init__.py
│       ├── security.py      # JWT handling
│       └── validators.py    # Input validation
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration
├── run.py                   # Application entry point
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Profile Service
```
profile-service/
├── app/
│   ├── __init__.py          # Factory pattern
│   ├── extensions.py        # SQLAlchemy initialization
│   ├── models/
│   │   ├── __init__.py
│   │   └── profile.py       # Profile model
│   ├── routes/
│   │   ├── __init__.py
│   │   └── profile_routes.py # Profile endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── profile_service.py # Business logic
│   └── middleware/
│       ├── __init__.py
│       └── auth_middleware.py # JWT verification
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration
├── run.py                   # Application entry point
├── requirements.txt
├── Dockerfile
└── .env.example
```

### API Gateway
```
api-gateway/
├── app/
│   ├── __init__.py          # Factory pattern
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py   # Auth proxy routes
│   │   ├── profile_routes.py # Profile proxy routes
│   │   └── health_routes.py # Health checks
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py # Header extraction
│   └── utils/
│       ├── __init__.py
│       └── service_proxy.py # Request forwarding
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration
├── run.py                   # Application entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml       # Orchestration
└── README.md                # Detailed documentation
```

##  Documentación Swagger

**URL:** http://localhost:5000/docs

Prueba todos los endpoints interactivamente desde el navegador.

## 📚 Endpoints Disponibles

### Authentication Service

#### POST `/api/auth/register`
Registrar un nuevo usuario (Paciente o Médico)

**Body:**
```json
{
  "nombre_completo": "Juan Pérez",
  "username": "juanperez",
  "email": "juan@example.com",
  "numero_celular": "1234567890",
  "password": "password123",
  "confirmar_password": "password123",
  "rol": "Paciente"
}
```

#### POST `/api/auth/login`
Iniciar sesión (acepta username o email)

**Body:**
```json
{
  "username": "juanperez",
  "password": "password123"
}
```

### Profile Service

> **Nota:** Todos los endpoints requieren token de autenticación en el header:
> `Authorization: Bearer <token>`

#### POST `/api/profile`
Crear perfil de usuario

**Body:**
```json
{
  "user_id": 1,
  "edad": 45,
  "peso": 75.5,
  "altura": 170,
  "medicamentos": "Metformina 500mg",
  "antecedentes": "Diabetes tipo 2",
  "fecha_diagnostico": "2020-05-15"
}
```

#### GET `/api/profile/{user_id}`
Obtener perfil por ID de usuario

#### PUT `/api/profile/{user_id}`
Actualizar perfil (todos los campos son opcionales)

**Body:**
```json
{
  "peso": 73.0,
  "medicamentos": "Metformina 500mg 3 veces al día"
}
```

## 🏗️ Arquitectura por Capas

Cada microservicio implementa una **arquitectura limpia por capas**:

- **Routes**: Endpoints HTTP (presentación)
- **Services**: Lógica de negocio
- **Models**: Modelos de datos
- **Middleware**: Autenticación y validación
- **Utils**: Utilidades reutilizables
- **Config**: Configuración centralizada

**Beneficios:**
- ✅ Código mantenible y escalable
- ✅ Fácil de testear
- ✅ Separación clara de responsabilidades
- ✅ No son pequeños monolitos

📚 **Para entender la arquitectura en detalle, consulta:** [`ARCHITECTURE.md`](ARCHITECTURE.md)

## 🧪 Pruebas con Postman

Importa la colección `Glucpred-API.postman_collection.json` en Postman para probar todos los endpoints fácilmente.

## 🗄️ Bases de Datos

- **auth_db** (puerto 3307): Base de datos del servicio de autenticación
- **profile_db** (puerto 3308): Base de datos del servicio de perfiles

## 🔐 Roles de Usuario

- **Paciente**: Usuario con diabetes tipo 2
- **Medico**: Profesional de la salud (endocrinólogo)

## 📖 Documentación Adicional

- **API Completa**: [`api-gateway/README.md`](api-gateway/README.md)
- **Arquitectura**: [`ARCHITECTURE.md`](ARCHITECTURE.md)