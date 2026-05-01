FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY packages/ /packages/

RUN pip install --no-cache-dir \
    -e /packages/llm \
    -e /packages/agents \
    -e /packages/rag \
    -e /packages/data \
    -e /packages/ml \
    -e /packages/geo \
    -e /packages/reports

COPY services/api/ /app/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
