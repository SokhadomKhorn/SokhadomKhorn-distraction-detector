FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir flask==3.0.0

COPY web_app.py .
COPY logger.py .
COPY templates/ ./templates/
COPY static/ ./static/

EXPOSE 5000

CMD ["python", "web_app.py"]
