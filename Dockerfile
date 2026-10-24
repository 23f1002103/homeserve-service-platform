FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS application

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /frontend/dist ./backend/app/static/

WORKDIR /app/backend

# Railway supplies PORT. The fallback makes the same image runnable locally.
CMD ["sh", "-c", "flask --app app:create_app db upgrade && exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 wsgi:app"]
