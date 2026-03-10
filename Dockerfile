FROM python:3.12-slim

# System dependencies pour Docling et OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    fonts-dejavu-core \
    libxcb1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files pour le cache Docker
COPY pyproject.toml uv.lock ./

# Install dependencies avec uv
RUN uv sync --frozen --no-install-project

# Pré-charger les modèles Docling dans l'image (évite cold start)
RUN .venv/bin/python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

# Copy le code
COPY handler.py .

# RunPod handler via le venv uv
CMD [".venv/bin/python", "handler.py"]