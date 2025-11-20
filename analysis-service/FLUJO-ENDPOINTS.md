# Flujo de Endpoints y Eventos: Analysis, Alerts y Records

## 1. Predicción de Episodio Glucémico

### Endpoint
- **POST** `/api/analysis/predict`
- **Acceso:** Solo usuarios autenticados con rol `paciente` (requiere JWT)

#### Request Body (JSON)
```
{
  "glucose": float,           // Requerido
  "insulin_30min": float,     // Requerido
  "carbs_30min": float,       // Requerido
  "user_id": string,          // Requerido
  "heart_rate": float,        // Opcional (default 70)
  "calories_15min": float,    // Opcional (default 5)
  "steps_15min": int,         // Opcional (default 50)
  "hour": int,                // Opcional (default actual)
  "timestamp": string         // Opcional (ISO)
}
```

### Proceso Interno
1. El usuario envía los datos al endpoint.
2. El analysis-service valida el JWT y el rol del usuario.
3. Se ejecuta la predicción usando el modelo ML.
4. Se genera la respuesta con la predicción, probabilidades, nivel de alerta y recomendación.

## 2. Emisión de Eventos al Event Bus (Kafka)

Tras cada predicción, el analysis-service emite dos eventos al topic de Kafka (`event-bus`):

### a) Evento de Alerta (`alert.created`)
- **Destino:** alerts-service
- **Payload:**
```
{
  "type": "alert.created",
  "user_id": string,
  "alert": {
    "prediction": string,
    "alert_level": string,
    "recommendation": string,
    "probabilities": { ... },
    "timestamp": string
  }
}
```

### b) Evento de Registro (`record.created`)
- **Destino:** records-service
- **Payload:**
```
{
  "type": "record.created",
  "user_id": string,
  "record": {
    "glucose": float,
    "insulin_30min": float,
    "carbs_30min": float,
    "heart_rate": float,
    "calories_15min": float,
    "steps_15min": int,
    "hour": int,
    "prediction": string,
    "probabilities": { ... },
    "timestamp": string
  }
}
```

## 3. Consumo de Eventos

### alerts-service
- Escucha eventos `alert.created` en Kafka.
- Al recibir uno, almacena la alerta en su base de datos y puede notificar al usuario.

### records-service
- Escucha eventos `record.created` en Kafka.
- Al recibir uno, almacena el registro histórico de la predicción y medición del usuario.

## 4. Resumen Visual del Flujo

```
Usuario (paciente)
      │
      ▼
[POST /api/analysis/predict]
      │
      ▼
analysis-service
      │
      ├── produce alert.created ───────────────► alerts-service (guarda alerta)
      │
      └── produce record.created ──────────────► records-service (guarda registro)
```

- Todo el flujo es asíncrono y desacoplado gracias a Kafka.
- El `user_id` viaja en cada evento para trazabilidad.
- Solo el analysis-service expone endpoint HTTP; los otros servicios solo consumen eventos.
