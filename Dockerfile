FROM python:3.10-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling packages like Prophet or bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . /app/

# Ensure required folders exist
RUN mkdir -p /app/instance /app/app/static/uploads /app/instance/models

# Expose port 5000 for Gunicorn
EXPOSE 5000

# Run Gunicorn WSGI server to host the app
CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
