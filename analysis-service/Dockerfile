FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Verificar que el modelo existe
RUN test -f models/episode_predictor.joblib || echo "WARNING: Model file not found"

EXPOSE 5000

CMD ["python", "run.py"]
