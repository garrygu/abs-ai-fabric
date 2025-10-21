FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for the integrated application
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_integrated.txt .
RUN pip install --no-cache-dir -r requirements_integrated.txt

# Copy application code
COPY . .

# Create comprehensive data directories for integrated storage
RUN mkdir -p /data/file_storage/{documents,analysis_results,reports,archives,templates,backups,temp,metadata} \
    && mkdir -p /data/uploads \
    && mkdir -p /data/reports \
    && mkdir -p /data/templates \
    && mkdir -p /data/logs

# Set proper permissions for data directories
RUN chmod -R 755 /data

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /data
USER appuser

# Expose port
EXPOSE 8080

# Health check for integrated application
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run the integrated application
CMD ["uvicorn", "app_integrated:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]