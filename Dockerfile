FROM python:3.10.6-slim

WORKDIR /app

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY . .

CMD uvicorn api.fast:app --host 0.0.0.0 --port ${PORT:-8080}
