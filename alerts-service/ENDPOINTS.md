# Alerts Service - Endpoints Documentation

## Base URL
`http://localhost:5000/api/alerts` (vía API Gateway)

---

## 🚨 Sistema de Alertas Automáticas

El sistema de alertas funciona de manera automática:

1. **CGM registra medición** → `POST /api/records/` 
2. **Records-service clasifica** → bajo/normal/alto/critico
3. **Kafka publica evento** → `glucose.recorded`
4. **Alerts-service escucha** → Crea alerta si es necesario
5. **Usuario ve alerta** → En app móvil (pestaña Alertas)

### Tipos de Alertas

#### 📍 Alertas Críticas (Automáticas por CGM)
- **Hiperglucemia detectada** (>180 mg/dL)
  - Severity: `critico` 🔴
  - Mensaje: "Revisar medicación y consultar médico"
  
- **Glucosa elevada** (140-180 mg/dL)
  - Severity: `advertencia` 🟡
  - Mensaje: "Nivel de glucosa alto. Monitorear y evitar carbohidratos"
  
- **Hipoglucemia severa** (<50 mg/dL)
  - Severity: `critico` 🔴
  - Mensaje: "Consumir 15g de carbohidratos rápidos inmediatamente"
  
- **Hipoglucemia leve** (50-70 mg/dL)
  - Severity: `advertencia` 🟡
  - Mensaje: "Consumir 15g de carbohidratos rápidos"

#### 🔔 Recordatorios (Manuales)
- Severity: `info` 🔵
- Ejemplo: "Tomar medicación", "Medición de glucosa"

---

## 📱 Endpoints para Pestaña ALERTAS

### 1. **Obtener Alertas (Con Filtros)**

```http
GET /api/alerts/?type={tipo}&severity={severidad}&is_read={leido}
```

**Descripción:** Obtiene las alertas del usuario autenticado con filtros por tipo, severidad y estado de lectura.

**Autenticación:** Bearer Token (JWT)

**Query Parameters:**
- `type` (opcional): Filtrar por tipo
  - `todas` (default) - Todas las alertas
  - `critica` - Solo alertas críticas de glucosa
  - `recordatorio` - Solo recordatorios
- `severity` (opcional): Filtrar por severidad
  - `critico` - Alertas críticas (rojo)
  - `advertencia` - Advertencias (amarillo)
  - `info` - Informativas (azul)
- `is_read` (opcional): Filtrar por estado de lectura
  - `true` - Solo leídas
  - `false` - Solo no leídas
- `limit` (opcional): Número de resultados (default: 100, max: 500)
- `offset` (opcional): Desplazamiento para paginación (default: 0)

**Ejemplos de uso para cada pestaña:**
- **📍 Todas:** `GET /api/alerts/?type=todas`
- **🔴 Críticas:** `GET /api/alerts/?type=critica`
- **🔔 Recordatorios:** `GET /api/alerts/?type=recordatorio`

**Response 200:**
```json
{
  "alerts": [
    {
      "id": 45,
      "user_id": 5,
      "glucose_record_id": 123,
      "glucose_value": 185.0,
      "alert_type": "critica",
      "severity": "critico",
      "title": "Hiperglucemia detectada",
      "message": "Revisar medicación y consultar médico.",
      "is_read": false,
      "is_dismissed": false,
      "created_at": "2025-11-16T10:30:00",
      "read_at": null,
      "dismissed_at": null
    },
    {
      "id": 46,
      "glucose_record_id": 124,
      "glucose_value": 68.0,
      "alert_type": "critica",
      "severity": "advertencia",
      "title": "Hipoglucemia leve",
      "message": "Consumir 15g de carbohidratos rápidos.",
      "is_read": false,
      "created_at": "2025-11-16T07:20:00"
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0,
  "has_more": false
}
```

---

### 2. **Contador de Alertas No Leídas**

```http
GET /api/alerts/unread-count
```

**Descripción:** Obtiene el número de alertas no leídas (para badge/notificación).

**Autenticación:** Bearer Token (JWT)

**Response 200:**
```json
{
  "unread_count": 3
}
```

**Uso en Frontend:**
```javascript
// Mostrar badge en icono de alertas
const badge = await fetch('/api/alerts/unread-count');
alertIcon.badge = badge.unread_count;  // "3"
```

---

### 3. **Contador de Alertas Críticas**

```http
GET /api/alerts/critical-count?hours={horas}
```

**Descripción:** Obtiene el número de alertas críticas en las últimas X horas. Útil para vista del médico.

**Autenticación:** Bearer Token (JWT)

**Query Parameters:**
- `hours` (opcional): Período en horas (default: 24)

**Response 200:**
```json
{
  "critical_count": 2,
  "period_hours": 24
}
```

**Uso:** Mostrar en vista del médico: "Paciente Juan: 2 alertas críticas hoy"

---

### 4. **Marcar Alerta como Leída**

```http
PUT /api/alerts/{alert_id}/read
```

**Descripción:** Marca una alerta específica como leída (cuando el usuario la abre).

**Autenticación:** Bearer Token (JWT)

**Path Parameters:**
- `alert_id`: ID de la alerta

**Response 200:**
```json
{
  "message": "Alerta marcada como leída",
  "alert": {
    "id": 45,
    "is_read": true,
    "read_at": "2025-11-16T11:00:00",
    ...
  }
}
```

**Uso en Frontend:**
```javascript
// Cuando usuario hace clic en una alerta
async function openAlert(alertId) {
  await fetch(`/api/alerts/${alertId}/read`, {method: 'PUT'});
  // Actualizar UI
}
```

---

### 5. **Marcar Todas como Leídas**

```http
PUT /api/alerts/read-all
```

**Descripción:** Marca todas las alertas del usuario como leídas (botón "Marcar todas como leídas").

**Autenticación:** Bearer Token (JWT)

**Response 200:**
```json
{
  "message": "3 alertas marcadas como leídas",
  "count": 3
}
```

---

### 6. **Descartar/Eliminar Alerta**

```http
DELETE /api/alerts/{alert_id}
```

**Descripción:** Descarta una alerta (deja de aparecer en la lista).

**Autenticación:** Bearer Token (JWT)

**Path Parameters:**
- `alert_id`: ID de la alerta

**Response 200:**
```json
{
  "message": "Alerta descartada exitosamente"
}
```

**Uso:** Botón de deslizar para eliminar en la app móvil.

---

### 7. **Crear Recordatorio Manual**

```http
POST /api/alerts/reminder
```

**Descripción:** Crea un recordatorio manual (no basado en glucosa).

**Autenticación:** Bearer Token (JWT)

**Request Body:**
```json
{
  "title": "Tomar medicación",
  "message": "Recuerda tomar tu insulina de la mañana"
}
```

**Response 201:**
```json
{
  "message": "Recordatorio creado exitosamente",
  "alert": {
    "id": 47,
    "user_id": 5,
    "alert_type": "recordatorio",
    "severity": "info",
    "title": "Tomar medicación",
    "message": "Recuerda tomar tu insulina de la mañana",
    "created_at": "2025-11-16T08:00:00"
  }
}
```

---

## 👨‍⚕️ Endpoints para Médicos

### 8. **Ver Alertas de un Paciente**

```http
GET /api/alerts/patient/{patient_id}?type={tipo}
```

**Descripción:** Médicos pueden ver las alertas de sus pacientes asignados.

**Autenticación:** Bearer Token (JWT - role: medico)

**Path Parameters:**
- `patient_id`: ID del paciente

**Query Parameters:** Igual que endpoint #1 (type, severity, limit, offset)

**Response 200:**
```json
{
  "patient_id": 15,
  "alerts": [
    {
      "id": 45,
      "glucose_value": 185.0,
      "title": "Hiperglucemia detectada",
      "severity": "critico",
      "created_at": "2025-11-16T10:30:00"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

---

### 9. **Contador de Alertas Críticas de Paciente**

```http
GET /api/alerts/patient/{patient_id}/critical-count?hours={horas}
```

**Descripción:** Médicos pueden ver el número de alertas críticas de un paciente.

**Autenticación:** Bearer Token (JWT - role: medico)

**Response 200:**
```json
{
  "patient_id": 15,
  "critical_count": 2,
  "period_hours": 24
}
```

**Uso:** Mostrar en la lista de pacientes del médico:
```javascript
// Vista del médico: Home > Pacientes
patients.forEach(async (patient) => {
  const alerts = await fetch(`/api/alerts/patient/${patient.id}/critical-count`);
  patient.alertas = alerts.critical_count;  // "Alertas: 2"
});
```

---

## 📱 Mapeo Frontend - Backend

### 🏠 Pestaña ALERTAS

**Componentes principales:**

1. **Filtros (Tabs):**
   - **Todas:** `GET /api/alerts/?type=todas`
   - **Críticas:** `GET /api/alerts/?type=critica`
   - **Recordatorios:** `GET /api/alerts/?type=recordatorio`

2. **Badge de Notificación (Icono):**
   - Endpoint: `GET /api/alerts/unread-count`
   - Mostrar: Círculo rojo con número "3"

3. **Lista de Alertas:**
   - Endpoint: `GET /api/alerts/?type={selectedTab}`
   - Mostrar: Título, mensaje, hora, valor de glucosa (si aplica)
   - Color según severity:
     - `critico` → Rojo (#FF0000)
     - `advertencia` → Amarillo (#FFA500)
     - `info` → Azul (#0066FF)

4. **Acción al hacer clic:**
   - Endpoint: `PUT /api/alerts/{id}/read`
   - Marcar como leída y quitar badge

5. **Deslizar para eliminar:**
   - Endpoint: `DELETE /api/alerts/{id}`

6. **Botón "Marcar todas como leídas":**
   - Endpoint: `PUT /api/alerts/read-all`

**Ejemplo de implementación:**
```javascript
// Cargar alertas según filtro seleccionado
async function loadAlerts(filterType) {
  const response = await fetch(`/api/alerts/?type=${filterType}`);
  const data = await response.json();
  
  data.alerts.forEach(alert => {
    // Mapear severity a color
    const color = {
      'critico': '#FF0000',
      'advertencia': '#FFA500',
      'info': '#0066FF'
    }[alert.severity];
    
    // Renderizar tarjeta de alerta
    renderAlertCard({
      title: alert.title,
      message: alert.message,
      time: formatTime(alert.created_at),
      glucose: alert.glucose_value ? `${alert.glucose_value} mg/dl` : null,
      color: color,
      badge: alert.severity === 'critico' ? 'Crítico' : 'Crítico',
      onClick: () => markAsRead(alert.id)
    });
  });
}

// Actualizar badge de notificaciones
async function updateBadge() {
  const response = await fetch('/api/alerts/unread-count');
  const data = await response.json();
  alertBadge.text = data.unread_count > 0 ? data.unread_count : '';
}

// Marcar como leída
async function markAsRead(alertId) {
  await fetch(`/api/alerts/${alertId}/read`, {method: 'PUT'});
  updateBadge();
}
```

---

### 👨‍⚕️ Vista del Médico - Home

**Mostrar "Alertas: 2" en cada paciente:**
```javascript
// Al cargar lista de pacientes
async function loadPatients() {
  const patients = await fetch('/api/doctor-patient/my-patients');
  
  for (const patient of patients) {
    // Obtener contador de alertas críticas del día
    const alerts = await fetch(`/api/alerts/patient/${patient.user_id}/critical-count?hours=24`);
    
    patient.alertasHoy = alerts.critical_count;
    // Mostrar: "Alertas: 2" (rojo si > 0)
  }
}
```

---

## 🔄 Flujo Completo (CGM → Alerta)

### Caso 1: Hiperglucemia detectada

1. **CGM mide glucosa:** 185 mg/dL a las 10:30 AM
2. **App envía a backend:**
   ```javascript
   POST /api/records/
   {
     "glucose_value": 185.0,
     "measurement_time": "2025-11-16T10:30:00Z"
   }
   ```

3. **Records-service:**
   - Clasifica: `critico` (>180)
   - Guarda en BD
   - Publica evento Kafka:
     ```json
     {
       "user_id": 5,
       "record_id": 123,
       "glucose_value": 185.0,
       "classification": "critico"
     }
     ```

4. **Alerts-service (automático):**
   - Escucha evento Kafka
   - Crea alerta:
     ```json
     {
       "title": "Hiperglucemia detectada",
       "message": "Revisar medicación y consultar médico",
       "severity": "critico",
       "glucose_value": 185.0
     }
     ```

5. **Frontend (app móvil):**
   - Recibe push notification (si implementado)
   - Badge de alertas aumenta: "3"
   - Usuario abre pestaña Alertas
   - Ve: "Hiperglucemia detectada - 10:30 AM - 185 mg/dl"

### Caso 2: Recordatorio manual

1. **Usuario crea recordatorio:**
   ```javascript
   POST /api/alerts/reminder
   {
     "title": "Tomar insulina",
     "message": "Dosis de la mañana"
   }
   ```

2. **Alerta se crea inmediatamente**
3. **Aparece en pestaña "Recordatorios"**

---

## 🎨 Colores y Estados

### Badges de Severity
```javascript
const severityStyles = {
  'critico': {
    bgColor: '#FF0000',
    textColor: '#FFFFFF',
    label: 'Crítico'
  },
  'advertencia': {
    bgColor: '#FFA500',
    textColor: '#000000',
    label: 'Crítico'  // Como en las imágenes
  },
  'info': {
    bgColor: '#0066FF',
    textColor: '#FFFFFF',
    label: 'Info'
  }
};
```

### Estados de Alerta
- **No leída:** Fondo blanco, texto bold
- **Leída:** Fondo gris claro, texto normal
- **Descartada:** No se muestra (eliminada)

---

## ⚠️ Códigos de Error

- `400` - Bad Request (datos inválidos)
- `401` - Unauthorized (token faltante o inválido)
- `403` - Forbidden (no es médico cuando se requiere)
- `404` - Not Found (alerta no encontrada)
- `500` - Internal Server Error

---

## 💡 Notas de Implementación

### 1. Deduplicación de Alertas
El sistema **NO crea alertas duplicadas** del mismo tipo en la última hora. 

Ejemplo: Si hay hiperglucemia a las 10:30 (185 mg/dL) y otra a las 10:45 (190 mg/dL), solo se crea **una alerta**.

### 2. Umbrales de Glucosa
```javascript
const thresholds = {
  hipoglucemiaSevera: 50,    // < 50 → "Hipoglucemia severa"
  hipoglucemiaLeve: 70,      // 50-70 → "Hipoglucemia leve"
  normal: [70, 140],         // 70-140 → Sin alerta
  hiperglucemiaAlta: 180,    // 140-180 → "Glucosa elevada"
  hiperglucemiaCritica: 180  // > 180 → "Hiperglucemia detectada"
};
```

### 3. Tiempo del Frontend vs Backend
- El backend trabaja en **UTC**
- El frontend debe convertir `created_at` a zona horaria local:
  ```javascript
  const localTime = new Date(alert.created_at).toLocaleTimeString();
  // "10:30 AM"
  ```

### 4. Paginación
Para listas largas, usar `limit` y `offset`:
```javascript
// Cargar 50 alertas a la vez
let offset = 0;
const limit = 50;

async function loadMore() {
  const alerts = await fetch(`/api/alerts/?limit=${limit}&offset=${offset}`);
  offset += limit;
  
  if (!alerts.has_more) {
    hideLoadMoreButton();
  }
}
```

### 5. Orden de Alertas
Las alertas se devuelven **más recientes primero** (ordenadas por `created_at DESC`).

---

## 🔐 Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer {token}
```

El token se obtiene del login (`POST /api/auth/login`)

---

## 🚀 Integración Completa

**Servicios involucrados:**
1. **Records-service** (Puerto 8085) - Recibe mediciones CGM
2. **Kafka** (Puerto 9092) - Bus de eventos
3. **Alerts-service** (Puerto 8086) - Procesa alertas
4. **API Gateway** (Puerto 5000) - Proxy unificado

**Flujo de datos:**
```
CGM → App Móvil → API Gateway → Records-service → Kafka → Alerts-service → BD
                                                               ↓
                                                         App Móvil (Alertas)
```
