# Imagen base ligera con Python
FROM python:3.13-slim

WORKDIR /app

# Primero las dependencias, para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py app.py ./

# Las tareas se guardan en /data, donde Kubernetes monta el volumen
ENV TAREAS_FILE=/data/tareas.json \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Servidor web; 0.0.0.0 para aceptar conexiones de fuera del contenedor
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
