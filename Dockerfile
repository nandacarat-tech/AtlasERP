FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Cria usuario e grupo nao-root para execucao segura do container
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser

# Copia e instala as dependencias com o usuario apropriado
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o codigo com ownership ja definido (evita duplicacao de camadas do Docker)
COPY --chown=appuser:appgroup . .

# Executa com usuario nao-root (principio do menor privilegio)
USER appuser

EXPOSE 8080

# Inicia o Gunicorn com timeout de 120s e envio de logs estruturados para stdout/stderr
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - "run:app"
