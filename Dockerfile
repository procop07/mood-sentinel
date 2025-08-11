# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cron job to run main.py every hour
RUN echo "0 * * * * cd /app && python main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/mood-sentinel

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/mood-sentinel

# Apply cron job
RUN crontab /etc/cron.d/mood-sentinel

# Create log file for cron
RUN touch /var/log/cron.log

# Expose port for API
EXPOSE 8000

# Create startup script that starts both cron and the API
RUN echo '#!/bin/bash\n\
service cron start\n\
exec python -m uvicorn app:app --host 0.0.0.0 --port 8000' > /app/start.sh
RUN chmod +x /app/start.sh

# Start both cron service and API
CMD ["/app/start.sh"]
