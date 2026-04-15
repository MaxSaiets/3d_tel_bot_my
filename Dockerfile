FROM python:3.11-slim

WORKDIR /app

COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
