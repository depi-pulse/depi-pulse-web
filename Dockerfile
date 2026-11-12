FROM python:3.12-slim
# SQLITE_PATH in /tmp: the container may run as a non-root user (Hugging Face uses uid 1000).
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_DEBUG=0 SQLITE_PATH=/tmp/db.sqlite3 PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --no-input && chmod +x start.sh
EXPOSE 8000
CMD ["./start.sh"]
