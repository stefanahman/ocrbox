FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 ocrbox && \
    mkdir -p /app/data/tokens /app/data/output /app/data/archive /app/data/watch && \
    chown -R ocrbox:ocrbox /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/

# Set proper permissions
RUN chown -R ocrbox:ocrbox /app

# Switch to non-root user
USER ocrbox

# Expose OAuth callback port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "src.main"]

