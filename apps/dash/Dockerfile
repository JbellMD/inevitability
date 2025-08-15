# apps/dash/Dockerfile
FROM python:3.11-slim

# System basics
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project (assumes monorepo layout)
COPY core core
COPY apps/dash/requirements.txt apps/dash/requirements.txt
COPY apps/dash/app.py apps/dash/app.py
COPY data data
COPY docs docs

# Python deps
RUN pip install --no-cache-dir -r apps/dash/requirements.txt

EXPOSE 8501
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
CMD ["streamlit", "run", "apps/dash/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
