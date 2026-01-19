FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY aquapark_occupancy.py .

# Set environment variables (can be overridden in docker-compose)
ENV SWIM_MQTT_BROKER=homeassistant.local
ENV SWIM_MQTT_PORT=1883
ENV SWIM_MQTT_USERNAME=mqtt_user
ENV SWIM_MQTT_PASSWORD=mqtt_password
ENV SWIM_MQTT_TOPIC_PREFIX=aquapark

# Run the script every 5 minutes using cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Create cron job
RUN echo "*/5 * * * * cd /app && /usr/local/bin/python aquapark_occupancy.py >> /var/log/aquapark.log 2>&1" > /etc/cron.d/aquapark-cron && \
    chmod 0644 /etc/cron.d/aquapark-cron && \
    crontab /etc/cron.d/aquapark-cron && \
    touch /var/log/aquapark.log

# Start cron in foreground
CMD ["cron", "-f"]
