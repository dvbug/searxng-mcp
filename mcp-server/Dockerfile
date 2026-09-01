FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv "$VIRTUAL_ENV"

COPY pyproject.toml ./pyproject.toml
RUN "$VIRTUAL_ENV/bin/python" -m pip install --upgrade pip setuptools wheel && \
    "$VIRTUAL_ENV/bin/python" -m pip install -e .

COPY ./mcp-server /app/mcp-server
COPY ./searxng /app/searxng

CMD ["/opt/venv/bin/python", "/app/mcp-server/main2.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000", "--streamable-http-path", "/mcp"]
