# Glucpred Backend - Microservices Architecture

Sistema de backend para la aplicación Glucpred basado en arquitectura de microservicios con Flask.

## 🏗️ Arquitectura

El sistema está compuesto por los siguientes servicios:

- **API Gateway** (Puerto 5000): Punto de entrada único que enruta las peticiones a los microservicios
- **Authentication Service** (Puerto 8081): Manejo de registro y autenticación de usuarios con JWT
- **Profile Service** (Puerto 8082): Gestión de perfiles de pacientes

Cada servicio tiene su propia base de datos MySQL y se ejecuta en un contenedor Docker independiente.

## 📋 Requisitos

- Docker
- Docker Compose
- Git

## 🚀 Inicio Rápido

```bash
cd api-gateway
docker-compose up --build
```

**Acceder a:**
- Swagger: http://localhost:5000/docs
- API Gateway: http://localhost:5000
- Health Check: http://localhost:5000/health

## 📚 Documentación de APIs

### Authentication Service

#### Registrar Usuario
```bash
POST /api/auth/register
Content-Type: application/json

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

**Respuesta exitosa (201):**
```json
{
  "message": "Usuario registrado exitosamente",
  "user": {
    "id": 1,
    "nombre_completo": "Juan Pérez",
    "username": "juanperez",
    "email": "juan@example.com",
    "numero_celular": "1234567890",
    "rol": "Paciente",
    "created_at": "2025-11-01T10:00:00"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "juanperez",
  "password": "password123"
}
```

**Nota:** El campo `username` acepta tanto el nombre de usuario como el correo electrónico.

**Respuesta exitosa (200):**
```json
{
  "message": "Login exitoso",
  "user": {
    "id": 1,
    "nombre_completo": "Juan Pérez",
    "username": "juanperez",
    "email": "juan@example.com",
    "rol": "Paciente"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Profile Service

**Nota:** Todos los endpoints de profile requieren autenticación. Incluir el token en el header:
```
Authorization: Bearer <access_token>
```

#### Crear Perfil
```bash
POST /api/profile
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "user_id": 1,
  "edad": 45,
  "peso": 75.5,
  "altura": 170,
  "medicamentos": "Metformina 500mg 2 veces al día",
  "antecedentes": "Diabetes tipo 2, hipertensión",
  "fecha_diagnostico": "2020-05-15"
}
```

**Respuesta exitosa (201):**
```json
{
  "message": "Perfil creado exitosamente",
  "profile": {
    "id": 1,
    "user_id": 1,
    "edad": 45,
    "peso": 75.5,
    "altura": 170,
    "imc": 26.12,
    "medicamentos": "Metformina 500mg 2 veces al día",
    "antecedentes": "Diabetes tipo 2, hipertensión",
    "fecha_diagnostico": "2020-05-15",
    "created_at": "2025-11-01T10:00:00",
    "updated_at": "2025-11-01T10:00:00"
  }
}
```

#### Obtener Perfil
```bash
GET /api/profile/{user_id}
Authorization: Bearer <access_token>
```

#### Actualizar Perfil
```bash
PUT /api/profile/{user_id}
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "peso": 73.0,
  "medicamentos": "Metformina 500mg 3 veces al día"
}
```

**Nota:** Todos los campos son opcionales en la actualización.

## 🔐 Roles de Usuario

El sistema soporta dos roles:

- **Paciente**: Usuario con diabetes tipo 2 que registra sus datos
- **Médico**: Profesional de la salud (endocrinólogo)

## 🗄️ Bases de Datos

### Authentication Database (auth_db)
- **Tabla:** `users`
- **Puerto:** 3307 (host) -> 3306 (container)

### Profile Database (profile_db)
- **Tabla:** `profiles`
- **Puerto:** 3308 (host) -> 3306 (container)

## 🛠️ Comandos Docker

```bash
# Ver logs
docker-compose logs -f [servicio]

# Detener servicios
docker-compose down

# Detener y eliminar datos
docker-compose down -v

# Reconstruir
docker-compose up --build
```

## 🔧 Configuración

Las variables de entorno pueden configurarse en los archivos `.env` de cada servicio. Ver los archivos `.env.example` como referencia.

### Variables importantes:

- `JWT_SECRET_KEY`: Clave secreta para firmar los tokens JWT (debe ser la misma en auth y profile)
- `DATABASE_URL`: Cadena de conexión a la base de datos MySQL
- `SECRET_KEY`: Clave secreta de Flask

## 🧪 Testing

### Probar el flujo completo:

1. **Registrar un usuario:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_completo": "María García",
    "username": "mariagarcia",
    "email": "maria@example.com",
    "numero_celular": "9876543210",
    "password": "password123",
    "confirmar_password": "password123",
    "rol": "Paciente"
  }'
```

2. **Hacer login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mariagarcia",
    "password": "password123"
  }'
```

3. **Crear perfil (usar el token del login):**
```bash
curl -X POST http://localhost:5000/api/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_AQUI>" \
  -d '{
    "user_id": 1,
    "edad": 50,
    "peso": 68.0,
    "altura": 165,
    "medicamentos": "Insulina",
    "antecedentes": "Diabetes tipo 2",
    "fecha_diagnostico": "2019-03-20"
  }'
```

4. **Obtener perfil:**
```bash
curl -X GET http://localhost:5000/api/profile/1 \
  -H "Authorization: Bearer <TOKEN_AQUI>"
```

## 📝 Notas

- El IMC (Índice de Masa Corporal) se calcula automáticamente a partir del peso y la altura
- Los tokens JWT expiran después de 24 horas
- Las contraseñas se almacenan hasheadas usando bcrypt
- Todos los endpoints de profile requieren autenticación

## 🐛 Troubleshooting

### Error de conexión a la base de datos
- Verificar que los contenedores de MySQL estén corriendo: `docker-compose ps`
- Revisar los logs: `docker-compose logs auth-db` o `docker-compose logs profile-db`

### Error 503 Service Unavailable
- Los servicios pueden tardar unos segundos en estar listos después de iniciarse
- Esperar a que los health checks pasen: `docker-compose ps`

### Error de token inválido
- Verificar que el JWT_SECRET_KEY sea el mismo en authentication-service y profile-service
- Verificar que el token esté en el formato correcto: `Bearer <token>`

## 📄 Licencia

[Especificar licencia]

## 👥 Contribuidores

[Lista de contribuidores]
