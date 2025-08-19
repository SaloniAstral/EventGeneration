FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file from infrastructure
COPY 05-infrastructure/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules from infrastructure
COPY 05-infrastructure/shared/ ./shared/
COPY 05-infrastructure/config/ ./config/
COPY 05-infrastructure/database/ ./database/
COPY 05-infrastructure/events/ ./events/

# Copy service-specific code
COPY 04-monitoring/ ./

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run the application
CMD ["python", "monitoring_dashboard.py"]
