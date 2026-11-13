# Qualité Entrevistar Digital. Imagem sem dependências de gravação de áudio.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY requirements-render.txt ./
RUN pip install --no-cache-dir -r requirements-render.txt
COPY . /app
RUN useradd -m -u 10001 entrevistador && mkdir -p /tmp/entrevistador-digital && chown -R entrevistador:entrevistador /tmp/entrevistador-digital
USER entrevistador
EXPOSE 10000
CMD ["sh", "-c", "uvicorn server:APP --host 0.0.0.0 --port ${PORT:-10000}"]
