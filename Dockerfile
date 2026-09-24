# Python version that pandas/numpy/scikit-learn all have prebuilt wheels for
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (better Docker layer caching — deps only reinstall if this file changes)
COPY backend/requirements.txt ./backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the project, preserving the same folder structure
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Run from inside backend/, same as locally — keeps relative paths to frontend/ working
WORKDIR /app/backend

# Render provides $PORT at runtime; gunicorn must bind to it
CMD gunicorn --bind 0.0.0.0:$PORT app:app