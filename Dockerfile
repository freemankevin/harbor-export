ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
EXPOSE 5001
ENV FLASK_DEBUG=false
CMD ["python", "app.py"]
