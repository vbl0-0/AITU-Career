FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
ARG INSTALL_SEMANTIC=false
COPY requirements-ai.txt requirements.txt ./
RUN if [ "$INSTALL_SEMANTIC" = "true" ]; then pip install --no-cache-dir -r requirements-ai.txt; fi
COPY . .
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m app.database.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
