FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/telegram/pyproject.toml /app/
RUN pip install --no-cache-dir -e .

COPY apps/telegram/ /app/

CMD ["python", "bot.py"]
