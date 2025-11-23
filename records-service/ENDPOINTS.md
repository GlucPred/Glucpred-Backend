# Records Service - Endpoints Documentation

## Base URL
`http://localhost:5000/api/records` (vía API Gateway)

---

## 📱 Endpoints para Pestaña INICIO (Home)

### 1. **Última Medición de Glucosa**

```http
GET /api/records/latest
```

**Descripción:** Obtiene la medición más reciente del usuario autenticado. Ideal para mostrar en la pantalla de inicio.

**Autenticación:** Bearer Token (JWT)

**Response 200:**
```json
{
  "id": 130,
  "user_id": 5,
  "glucose_value": 103.0,
  "measurement_time": "2025-11-16T20:00:00",
  "classification": "normal",
  "created_at": "2025-11-16T20:01:00"
}
```

**Uso en la UI de Inicio:**
- Mostrar valor principal: "103 mg/dL"
- Mostrar estado: "Nivel normal" (basado en `classification`)
- Mostrar hora: "Última medición: 20:00"

---

### 2. **Registrar Nueva Medición**

```http
POST /api/records/
```

**Descripción:** Crea un nuevo registro de medición de glucosa desde el CGM (Continuous Glucose Monitor).

**Autenticación:** Bearer Token (JWT)

**Request Body:**
```json
{
  "glucose_value": 105.5,
  "measurement_time": "2025-11-16T14:30:00Z"  // Opcional (default: ahora)
}
```

**Response 201:**
```json
{
  "message": "Registro de glucosa creado exitosamente",
  "record": {
    "id": 131,
    "user_id": 5,
    "glucose_value": 105.5,
    "measurement_time": "2025-11-16T14:30:00",
    "classification": "normal",
    "created_at": "2025-11-16T14:30:15"
  }
}
```

**Clasificación Automática:**
- `bajo` → glucose_value < 70 mg/dL (Hipoglucemia) - ⚠️ Alerta roja
- `normal` → 70 ≤ glucose_value ≤ 140 mg/dL - ✅ Verde
- `alto` → 140 < glucose_value ≤ 180 mg/dL - ⚠️ Amarillo
- `critico` → glucose_value > 180 mg/dL - 🚨 Rojo crítico

---

### 3. **Estadísticas Rápidas (Vista Resumida)**

```http
GET /api/records/statistics?hours=24
```

**Descripción:** Obtiene estadísticas del día actual para mostrar en tarjetas de la pantalla de inicio.

**Autenticación:** Bearer Token (JWT)

**Response 200:**
```json
{
  "period_hours": 24,
  "total_readings": 8,
  "average": 126.5,
  "min": 88.0,
  "max": 167.0,
  "classifications": {
    "normal": 5,
    "alto": 2,
    "critico": 1,
    "bajo": 0
  },
  "last_reading": {
    "id": 130,
    "glucose_value": 103.0,
    "measurement_time": "2025-11-16T20:00:00",
    "classification": "normal"
  }
}
```

**Uso en Tarjetas de Inicio:**
```javascript
// Tarjeta "Promedio Hoy"
promedio.text = `${stats.average.toFixed(0)} mg/dL`;

// Tarjeta "Lecturas Hoy"
lecturas.text = `${stats.total_readings} mediciones`;

// Tarjeta "Estado General"
const porcentajeNormal = (stats.classifications.normal / stats.total_readings) * 100;
estado.text = porcentajeNormal > 70 ? "Bien controlado" : "Requiere atención";
```

---

## 📊 Endpoints para Pestaña GRÁFICA (Tendencias y Reportes)

### 4. **Tendencia de Glucosa (Para Gráficos)**

```http
GET /api/records/trend?hours={horas}
```

**Descripción:** Obtiene las mediciones de glucosa en un período de tiempo específico. Ideal para generar gráficos de tendencia en las pestañas Hoy/Semana/Mes.

**Autenticación:** Bearer Token (JWT)

**Query Parameters:**
- `hours` (opcional): Número de horas hacia atrás (default: 12, rango: 1-720)

**Ejemplos de uso para cada pestaña:**
- **📅 Hoy (24 horas):** `GET /api/records/trend?hours=24`
- **📅 Semana (7 días):** `GET /api/records/trend?hours=168`
- **📅 Mes (30 días):** `GET /api/records/trend?hours=720`

**Response 200:**
```json
{
  "user_id": 5,
  "period_hours": 24,
  "records": [
    {
      "id": 123,
      "user_id": 5,
      "glucose_value": 95.0,
      "measurement_time": "2025-11-16T06:00:00",
      "classification": "normal",
      "created_at": "2025-11-16T06:01:00"
    },
    {
      "id": 124,
      "glucose_value": 110.0,
      "measurement_time": "2025-11-16T10:00:00",
      "classification": "normal"
    },
    {
      "id": 125,
      "glucose_value": 145.0,
      "measurement_time": "2025-11-16T14:00:00",
      "classification": "alto"
    }
  ],
  "total": 3
}
```

---

### 5. **Estadísticas de Glucosa (Para Métricas)**

```http
GET /api/records/statistics?hours={horas}
```

**Descripción:** Calcula estadísticas agregadas para mostrar en las tarjetas de métricas de la pestaña Gráfica (Promedio, Mínimo, Máximo, % en rango).

**Autenticación:** Bearer Token (JWT)

**Query Parameters:**
- `hours` (opcional): Período en horas (default: 24, rango: 1-720)

**Ejemplos de uso para cada pestaña:**
- **📊 Hoy:** `GET /api/records/statistics?hours=24`
- **📊 Semana:** `GET /api/records/statistics?hours=168`
- **📊 Mes:** `GET /api/records/statistics?hours=720`

**Response 200:**
```json
{
  "period_hours": 24,
  "total_readings": 8,
  "average": 126.5,
  "min": 88.0,
  "max": 167.0,
  "classifications": {
    "normal": 5,
    "alto": 2,
    "critico": 1,
    "bajo": 0
  },
  "last_reading": {
    "id": 130,
    "glucose_value": 103.0,
    "measurement_time": "2025-11-16T20:00:00",
    "classification": "normal"
  }
}
```

**Uso en el Frontend (Pestaña Gráfica):**
- `average` → **Tarjeta "Promedio":** "127 mg/dL"
- `min` / `max` → **Tarjetas "Mínimo/Máximo":** "88" / "167"
- `classifications` → **Tarjeta "% en rango":** Calcular (normal/total * 100)
- `total_readings` → Para cálculos de porcentajes

**Cálculo % en rango objetivo:**
```javascript
const percentage = (classifications.normal / total_readings) * 100;
// Ejemplo: (5 / 8) * 100 = 62.5% → Mostrar "62%"
```

---

### 6. **Historial Paginado (Tabla de Registros)**

```http
GET /api/records/history?limit={limit}&offset={offset}&start_date={fecha}&end_date={fecha}
```

**Descripción:** Obtiene historial completo con paginación y filtros por fecha.

**Autenticación:** Bearer Token (JWT)

**Query Parameters:**
- `limit` (opcional): Registros por página (default: 100, max: 500)
- `offset` (opcional): Desplazamiento (default: 0)
- `start_date` (opcional): Fecha inicial ISO 8601
- `end_date` (opcional): Fecha final ISO 8601

**Ejemplo:**
```http
GET /api/records/history?limit=50&offset=0&start_date=2025-11-01T00:00:00Z&end_date=2025-11-30T23:59:59Z
```

**Response 200:**
```json
{
  "records": [
    {
      "id": 130,
      "glucose_value": 103.0,
      "measurement_time": "2025-11-16T20:00:00",
      "classification": "normal"
    },
    // ... más registros
  ],
  "total": 245,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

---

### 7. **Eliminar Registro**

```http
DELETE /api/records/{record_id}
```

**Descripción:** Elimina un registro de glucosa (solo propios registros). Útil para corregir mediciones incorrectas.

**Autenticación:** Bearer Token (JWT)

**Path Parameters:**
- `record_id`: ID del registro a eliminar

**Response 200:**
```json
{
  "message": "Registro eliminado exitosamente"
}
```

---

## 🔄 Gestión de Datos (Ambas Pestañas)

---

## 👨‍⚕️ Endpoints para Médicos (Ver datos de pacientes)

Estos endpoints permiten a los médicos ver los datos de sus pacientes asignados.

### 8. **Última Medición de un Paciente**

```http
GET /api/records/user/{patient_user_id}/latest
```

**Descripción:** Médicos pueden ver la última medición de cualquier paciente.

**Autenticación:** Bearer Token (JWT - role: medico)

**Path Parameters:**
- `patient_user_id`: ID del paciente

**Response:** Igual que `/latest`

---

### 9. **Tendencia de un Paciente**

```http
GET /api/records/user/{patient_user_id}/trend?hours={horas}
```

**Descripción:** Médicos pueden ver la tendencia de glucosa de sus pacientes.

**Response:** Igual que `/trend`

---

### 10. **Estadísticas de un Paciente**

```http
GET /api/records/user/{patient_user_id}/statistics?hours={horas}
```

**Descripción:** Médicos pueden ver estadísticas de sus pacientes.

**Response:** Igual que `/statistics`

---

### 11. **Historial de un Paciente**

```http
GET /api/records/user/{patient_user_id}/history?limit={limit}&offset={offset}
```

**Descripción:** Médicos pueden ver el historial completo de sus pacientes.

**Response:** Igual que `/history`

---

## 📱 Mapeo Frontend - Backend por Pestaña

### 🏠 Pestaña INICIO

**Componentes principales:**
1. **Glucosa Actual (Grande):**
   - Endpoint: `GET /api/records/latest`
   - Mostrar: `glucose_value` + `classification` (color)
   
2. **Sincronización con CGM:**
   - Endpoint: `POST /api/records/`
   - Enviar automáticamente: `glucose_value`, `measurement_time` desde el dispositivo CGM

3. **Tarjetas de Resumen del Día:**
   - Endpoint: `GET /api/records/statistics?hours=24`
   - Mostrar: `average`, `total_readings`, calcular % en rango

**Ejemplo de implementación:**
```javascript
// Cargar vista de inicio
async function loadHome() {
  // Última medición
  const latest = await fetch('/api/records/latest');
  glucosaActual.value = latest.glucose_value;
  glucosaActual.color = getColor(latest.classification);
  
  // Resumen del día
  const stats = await fetch('/api/records/statistics?hours=24');
  promedioHoy.value = stats.average.toFixed(0);
  lecturasHoy.value = stats.total_readings;
}

// Sincronización automática desde CGM
async function syncCGMReading(cgmData) {
  await fetch('/api/records/', {
    method: 'POST',
    body: JSON.stringify({
      glucose_value: cgmData.glucose,
      measurement_time: cgmData.timestamp
    })
  });
}
```

---

### 📊 Pestaña GRÁFICA

**Botones de período:**
- **Hoy:** `GET /api/records/trend?hours=24`
- **Semana:** `GET /api/records/trend?hours=168` (7 días * 24 horas)
- **Mes:** `GET /api/records/trend?hours=720` (30 días * 24 horas)

**Estadísticas mostradas:**
```javascript
// Llamar al endpoint
const stats = await fetch('/api/records/statistics?hours=24');

// Mapear a la UI
promedio.value = stats.average;           // "127 mg/dL"
minimo.value = stats.min;                 // "88 mg/dL"
maximo.value = stats.max;                 // "167 mg/dL"

// Calcular % en rango
const porcentajeEnRango = (stats.classifications.normal / stats.total_readings) * 100;
// "71%"
```

**Gráfico de niveles:**
```javascript
// Obtener datos
const data = await fetch('/api/records/trend?hours=24');

// Procesar para el gráfico
const chartData = data.records.map(r => ({
  x: r.measurement_time,  // Eje X: tiempo
  y: r.glucose_value,     // Eje Y: glucosa
  color: getColorByClassification(r.classification)
}));

function getColorByClassification(classification) {
  switch(classification) {
    case 'bajo': return '#FF0000';      // Rojo (Hipoglucemia)
    case 'normal': return '#00FF00';    // Verde
    case 'alto': return '#FFFF00';      // Amarillo (Precaución)
    case 'critico': return '#FF0000';   // Rojo (Crítico)
  }
}
```

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación JWT en el header:

```http
Authorization: Bearer {token}
```

El token se obtiene del login (`POST /api/auth/login`)

---

## ⚠️ Códigos de Error

- `400` - Bad Request (datos inválidos)
- `401` - Unauthorized (token faltante o inválido)
- `404` - Not Found (no hay registros)
- `500` - Internal Server Error

---

## 💡 Notas de Implementación

1. **Tiempo del Frontend vs Backend:**
   - El backend siempre trabaja en UTC
   - El frontend debe convertir a la zona horaria local del usuario

2. **Rangos de Glucosa (mg/dL):**
   - Bajo (Hipoglucemia): < 70
   - Normal: 70 - 140
   - Alto (Precaución): 140 - 180  
   - Crítico: > 180

3. **Límites de Consulta:**
   - Máximo 720 horas (30 días) para tendencias
   - Máximo 500 registros por página en historial

4. **Performance:**
   - Para gráficos en tiempo real, usar `/trend` con `hours` pequeño (12-24)
   - Para reportes históricos, usar `/history` con paginación
