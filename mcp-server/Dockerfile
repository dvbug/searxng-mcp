FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv "$VIRTUAL_ENV"

COPY requirements.txt ./requirements.txt
RUN "$VIRTUAL_ENV/bin/python" -m pip install --upgrade pip setuptools wheel && \
    "$VIRTUAL_ENV/bin/python" -m pip install -r requirements.txt

COPY . /app

CMD ["/opt/venv/bin/python", "/app/main.py"]
