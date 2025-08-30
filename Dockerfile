FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy chart generation code
COPY kerykeion_chart_generator.py .
COPY dynamic-natal-generator.py .
COPY chart_service.py .

# Create Swiss Ephemeris directory
RUN mkdir -p /usr/share/swisseph

# Set environment for Swiss Ephemeris
ENV SWISSEPH_PATH=/usr/share/swisseph

# Expose port
EXPOSE 5000

# Run the Flask service
CMD ["python", "chart_service.py"]