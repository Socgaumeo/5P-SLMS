FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Limit thread usage for numpy/pandas OpenBLAS (prevents crash on Railway)
ENV OPENBLAS_NUM_THREADS=1
ENV OMP_NUM_THREADS=1

EXPOSE 8000

CMD ["gunicorn", "main:app", "-c", "gunicorn_conf.py"]
