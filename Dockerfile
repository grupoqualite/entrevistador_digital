# Render: criação MANUAL de Web Service no plano Free. Não usar Blueprint.
# Modelo tiny multilíngue embutido na imagem, transcrição experimental em CPU.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    ENTREVISTADOR_WHISPER_MODEL=/opt/whisper/tiny \
    ENTREVISTADOR_ENV=production \
    ENTREVISTADOR_DATA=/tmp/entrevistador-digital \
    ENTREVISTADOR_OLLAMA_MODEL=""
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates ffmpeg fonts-dejavu-core libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements-render.txt ./
RUN pip install --no-cache-dir -r requirements-render.txt
# Baixa modelo (~78 MB) durante o build; execução não precisa acessar Hugging Face.
RUN mkdir -p /opt/whisper/tiny && \
    HF_HUB_OFFLINE=0 python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-tiny',local_dir='/opt/whisper/tiny')" && \
    test -s /opt/whisper/tiny/model.bin
RUN groupadd --gid 10001 entrevistador && useradd --uid 10001 --gid entrevistador --home-dir /app --shell /usr/sbin/nologin entrevistador && \
    mkdir -p /tmp/entrevistador-digital && chown -R entrevistador:entrevistador /tmp/entrevistador-digital
COPY --chown=entrevistador:entrevistador . /app
USER entrevistador
EXPOSE 10000
CMD ["python", "render_entrypoint.py"]
