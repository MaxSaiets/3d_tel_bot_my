FROM python:3.11-slim

WORKDIR /app

COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY pyproject.toml README.md /app/
COPY entrypoint.sh /app/entrypoint.sh

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && sed -i 's/\r//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["/app/entrypoint.sh"]
