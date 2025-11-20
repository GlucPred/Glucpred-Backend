# Analysis Service Endpoints

## POST /api/analysis/predict

Predice episodio glucémico y emite eventos para alertas y registros.

### Seguridad
- Solo usuarios autenticados con rol `paciente` pueden acceder (JWT requerido).

### Request
- **Content-Type:** application/json
- **Body:**
```
{
  "glucose": float,           // Glucosa actual (mg/dL) [requerido]
  "insulin_30min": float,     // Insulina administrada últimos 30 min [requerido]
  "carbs_30min": float,       // Carbohidratos ingeridos últimos 30 min [requerido]
  "user_id": string,          // ID del usuario [requerido]
  "heart_rate": float,        // Frecuencia cardíaca actual (opcional, default 70)
  "calories_15min": float,    // Calorías quemadas últimos 15 min (opcional, default 5)
  "steps_15min": int,         // Pasos últimos 15 min (opcional, default 50)
  "hour": int,                // Hora actual (opcional, default actual)
  "timestamp": string         // Timestamp ISO (opcional)
}
```

### Response
- **Content-Type:** application/json
- **Body:**
```
{
  "prediction": "Normal" | "Hipoglucemia" | "Hiperglucemia",
  "probabilities": {
    "Normal": float,
    "Hipoglucemia": float,
    "Hiperglucemia": float
  },
  "alert_level": "Bajo" | "Medio" | "Alto",
  "recommendation": string,
  "input_summary": {
    "glucose": float,
    "insulin_30min": float,
    "carbs_30min": float,
    "hour": int
  }
}
```

### Flujo de eventos
- Tras cada predicción:
  - Se emite un evento `alert.created` al event bus (Kafka) para que el alerts-service lo procese y almacene la alerta.
  - Se emite un evento `record.created` al event bus para que el records-service lo almacene como registro histórico.
- Ambos eventos incluyen el `user_id` para trazabilidad.

### Ejemplo de uso

**Request:**
```
curl -X POST http://localhost:5001/api/analysis/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT>" \
  -d '{
    "glucose": 110,
    "insulin_30min": 2,
    "carbs_30min": 15,
    "user_id": "1234"
  }'
```

**Response:**
```
{
  "prediction": "Normal",
  "probabilities": {
    "Normal": 0.85,
    "Hipoglucemia": 0.10,
    "Hiperglucemia": 0.05
  },
  "alert_level": "Bajo",
  "recommendation": "✅ Glucosa se mantendrá NORMAL (85.0%)\n→ Continuar monitoreo regular",
  "input_summary": {
    "glucose": 110.0,
    "insulin_30min": 2.0,
    "carbs_30min": 15.0,
    "hour": 14
  }
}
```
