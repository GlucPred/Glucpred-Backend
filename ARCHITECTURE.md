# Arquitectura de Microservicios - Glucpred Backend

## 🏛️ Diseño Arquitectónico

Este proyecto implementa una **arquitectura de microservicios** siguiendo los principios de **separación de responsabilidades** y **diseño por capas**. Cada servicio es independiente, escalable y mantiene su propia base de datos.

## 📊 Capas de la Arquitectura

### 1. **API Gateway** (Patrón Gateway)
El punto de entrada único para todas las peticiones del cliente.

**Responsabilidades:**
- Enrutamiento de peticiones a los microservicios
- Extracción y forwarding de headers de autenticación
- Health checks de todos los servicios
- Gestión centralizada de errores

**Estructura:**
```
app/
├── routes/          # Definición de endpoints proxy
├── middleware/      # Extracción de headers
└── utils/           # Lógica de forwarding
```

---

### 2. **Authentication Service**

Microservicio dedicado a la autenticación y gestión de usuarios.

#### Capas Implementadas:

**📁 Models (Capa de Datos)**
- `user.py`: Modelo SQLAlchemy del usuario
- Manejo de hash de contraseñas
- Conversión a diccionarios

**🔀 Routes (Capa de Presentación)**
- `auth_routes.py`: Endpoints REST (register, login)
- Validación de entrada HTTP
- Formateo de respuestas JSON

**💼 Services (Capa de Lógica de Negocio)**
- `auth_service.py`: Lógica de registro y autenticación
- Validación de reglas de negocio
- Coordinación entre modelos y utilidades

**🔧 Utils (Capa de Utilidades)**
- `security.py`: Generación y verificación de JWT
- `validators.py`: Validadores de datos de entrada

**⚙️ Config**
- `settings.py`: Configuración centralizada
- Variables de entorno
- Constantes de la aplicación

**Beneficios:**
- ✅ Lógica de negocio separada de las rutas
- ✅ Modelos reutilizables
- ✅ Seguridad encapsulada
- ✅ Fácil testing de cada capa

---

### 3. **Profile Service**

Microservicio para gestión de perfiles de pacientes.

#### Capas Implementadas:

**📁 Models (Capa de Datos)**
- `profile.py`: Modelo SQLAlchemy del perfil
- Cálculo automático de IMC
- Conversión a diccionarios

**🔀 Routes (Capa de Presentación)**
- `profile_routes.py`: Endpoints REST (CRUD de perfiles)
- Protección con decorador `@token_required`
- Manejo de respuestas

**💼 Services (Capa de Lógica de Negocio)**
- `profile_service.py`: CRUD de perfiles
- Validación de datos del perfil
- Parseo de fechas

**🛡️ Middleware**
- `auth_middleware.py`: Verificación de JWT
- Decorador reutilizable para proteger rutas

**⚙️ Config**
- `settings.py`: Configuración del servicio

**Beneficios:**
- ✅ Middleware reutilizable para autenticación
- ✅ Lógica de negocio independiente
- ✅ Separación clara de responsabilidades

---

## 🎯 Principios de Diseño Aplicados

### 1. **Separation of Concerns (SoC)**
Cada capa tiene una responsabilidad única:
- **Routes**: Manejo HTTP (request/response)
- **Services**: Lógica de negocio
- **Models**: Persistencia de datos
- **Utils/Middleware**: Funcionalidades transversales

### 2. **Single Responsibility Principle (SRP)**
Cada clase/módulo tiene una única razón para cambiar:
- `AuthService` solo maneja autenticación
- `JWTHandler` solo maneja tokens
- `AuthValidator` solo valida datos

### 3. **Dependency Inversion**
Las capas dependen de abstracciones:
- Routes dependen de Services (no de Models directamente)
- Services dependen de Models (no de detalles de BD)

### 4. **Factory Pattern**
- `create_app()`: Inicialización flexible de la aplicación
- Facilita testing y múltiples entornos

### 5. **Decorator Pattern**
- `@token_required`: Autenticación reutilizable
- `@extract_auth_header`: Extracción de headers

---

## 🔄 Flujo de una Petición

### Ejemplo: Crear un Perfil

```
1. Cliente → API Gateway
   POST /api/profile
   Headers: Authorization: Bearer <token>
   Body: { user_id, edad, peso, ... }

2. API Gateway → Profile Service
   - Extrae el token del header (@extract_auth_header)
   - Forward la petición al Profile Service

3. Profile Service → Route Layer
   - profile_routes.py recibe la petición
   - @token_required verifica el JWT

4. Route Layer → Service Layer
   - Llama a ProfileService.create_profile(data)
   
5. Service Layer → Business Logic
   - Valida que user_id exista
   - Verifica que no haya perfil duplicado
   - Parsea la fecha de diagnóstico

6. Service Layer → Model Layer
   - Crea instancia de Profile
   - Calcula IMC automáticamente
   
7. Model Layer → Database
   - SQLAlchemy persiste en MySQL

8. Response Flow (inverso)
   Database → Model → Service → Route → Gateway → Cliente
```

---

## 🧪 Ventajas para Testing

### Por Capas:
```python
# Test unitario del servicio (sin BD)
def test_auth_service_validation():
    result, error = AuthValidator.validate_registration(invalid_data)
    assert result == False

# Test de integración (con BD)
def test_create_profile():
    profile, error = ProfileService.create_profile(valid_data)
    assert profile is not None

# Test de endpoint (HTTP)
def test_register_endpoint(client):
    response = client.post('/api/auth/register', json=data)
    assert response.status_code == 201
```

---

## 📈 Escalabilidad

### Horizontal Scaling
Cada servicio puede escalar independientemente:
```yaml
# docker-compose.yml
authentication-service:
  replicas: 3  # Escalar según carga

profile-service:
  replicas: 2
```

### Database per Service
Cada servicio tiene su propia BD:
- `auth_db`: Solo para authentication-service
- `profile_db`: Solo para profile-service
- **No hay acoplamiento** entre bases de datos

---

## 🔐 Seguridad por Capas

1. **API Gateway**: Punto de entrada único
2. **JWT Verification**: En Profile Service
3. **Password Hashing**: En User Model
4. **Input Validation**: En Validators
5. **SQL Injection Protection**: SQLAlchemy ORM

---

## 🚀 Extensibilidad

### Agregar un nuevo endpoint:
1. **Route**: Define el endpoint en `routes/`
2. **Service**: Implementa la lógica en `services/`
3. **Model**: Si es necesario, actualiza en `models/`

### Agregar un nuevo microservicio:
1. Copia la estructura de carpetas
2. Define tus modelos
3. Implementa tus servicios
4. Crea tus rutas
5. Agrega al docker-compose.yml
6. Registra en API Gateway

---

## 📝 Comparación: Antes vs Después

### ❌ Antes (Monolito por servicio)
```
authentication-service/
├── app.py       # Todo mezclado
├── models.py    # Solo modelos
├── routes.py    # Solo rutas
└── config.py    # Solo config
```

**Problemas:**
- Lógica de negocio en las rutas
- Difícil de testear
- Acoplamiento alto
- No escalable

### ✅ Después (Arquitectura por Capas)
```
authentication-service/
├── app/
│   ├── models/      # Datos
│   ├── services/    # Lógica de negocio
│   ├── routes/      # Presentación
│   └── utils/       # Utilidades
└── config/          # Configuración
```

**Beneficios:**
- Responsabilidades claras
- Fácil de testear cada capa
- Bajo acoplamiento
- Alta cohesión
- Escalable y mantenible

---

## 🎓 Conceptos Clave

- **Microservicio ≠ Monolito pequeño**: Cada servicio debe tener arquitectura interna clara
- **Service Layer**: Contiene la lógica de negocio, no las rutas
- **Thin Routes**: Las rutas solo orquestan, no implementan lógica
- **Fat Models**: Los modelos pueden tener métodos útiles (como `calculate_imc()`)
- **Reusable Middleware**: Decoradores para funcionalidad transversal

---

## 📚 Referencias

- [Microservices Pattern](https://microservices.io/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Flask Application Factory](https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/)
- [Separation of Concerns](https://en.wikipedia.org/wiki/Separation_of_concerns)
