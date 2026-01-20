FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY aquapark_occupancy.py .

# Make script executable
RUN chmod +x aquapark_occupancy.py

# Set environment variables (can be overridden in docker-compose)
ENV SWIM_MQTT_BROKER=homeassistant.local
ENV SWIM_MQTT_PORT=1883
ENV SWIM_MQTT_USERNAME=mqtt_user
ENV SWIM_MQTT_PASSWORD=mqtt_password
ENV SWIM_MQTT_TOPIC_PREFIX=aquapark
ENV SWIM_SLEEP_INTERVAL=300

# Run the script in continuous mode
CMD ["python", "-u", "aquapark_occupancy.py"]
