# Aquapark Occupancy Monitor for Home Assistant

This script monitors the current occupancy of pools at www.aquavparku.cz and publishes the data to Home Assistant via MQTT.

## Features

- Parses occupancy data for 4 zones: Swimming Pool, Fun Zone, Wellness, and Exterior
- Only runs during operating hours (9:00-20:30 Prague time)
- Publishes data to MQTT for Home Assistant integration
- Timezone-aware scheduling using Prague (Europe/Prague) timezone
- Environment variable configuration with `SWIM_` prefix
- Docker support for easy deployment

## Deployment Options

You can deploy this in two ways:
1. **Docker (Recommended)** - Run alongside Home Assistant in Docker
2. **Manual Installation** - Run directly on your system with cron

---

## Option 1: Docker Deployment (Recommended)

### Using Pre-built Image from GitHub Container Registry

The easiest way to deploy is using the pre-built Docker image:

```yaml
services:
  aquapark-monitor:
    image: ghcr.io/rplevka/aquapark-occupancy:latest
    container_name: aquapark-monitor
    restart: unless-stopped
    environment:
      - SWIM_MQTT_BROKER=192.168.1.100
      - SWIM_MQTT_PORT=1883
      - SWIM_MQTT_USERNAME=your_mqtt_user
      - SWIM_MQTT_PASSWORD=your_mqtt_password
      - SWIM_MQTT_TOPIC_PREFIX=aquapark
      - TZ=Europe/Prague
    networks:
      - homeassistant
    volumes:
      - ./aquapark-logs:/var/log
```

Then run:
```bash
docker-compose up -d
```

### Building from Source

### 1. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your MQTT settings:

```bash
SWIM_MQTT_BROKER=192.168.1.100  # Your Home Assistant IP
SWIM_MQTT_PORT=1883
SWIM_MQTT_USERNAME=your_mqtt_user
SWIM_MQTT_PASSWORD=your_mqtt_password
SWIM_MQTT_TOPIC_PREFIX=aquapark
```

### 2. Deploy with Docker Compose

**If you already have Home Assistant running in Docker:**

Add the aquapark-monitor service to your existing `docker-compose.yml`:

```yaml
services:
  aquapark-monitor:
    image: ghcr.io/rplevka/aquapark-occupancy:latest
    # Or build from source:
    # build: /path/to/aquapark-occupancy
    container_name: aquapark-monitor
    restart: unless-stopped
    environment:
      - SWIM_MQTT_BROKER=${SWIM_MQTT_BROKER}
      - SWIM_MQTT_PORT=${SWIM_MQTT_PORT}
      - SWIM_MQTT_USERNAME=${SWIM_MQTT_USERNAME}
      - SWIM_MQTT_PASSWORD=${SWIM_MQTT_PASSWORD}
      - SWIM_MQTT_TOPIC_PREFIX=${SWIM_MQTT_TOPIC_PREFIX}
      - TZ=Europe/Prague
    networks:
      - homeassistant
    volumes:
      - ./aquapark-logs:/var/log
```

**Or use the provided docker-compose.yml:**

```bash
cd /Users/roman.plevka/CascadeProjects
docker-compose up -d
```

### 3. View Logs

```bash
docker logs -f aquapark-monitor
# Or check the log file
tail -f logs/aquapark.log
```

### 4. Configure Home Assistant

Add the contents of `homeassistant_config.yaml` to your Home Assistant `configuration.yaml` and restart Home Assistant.

---

## Option 2: Manual Installation

### Setup

### 1. Install Dependencies

```bash
cd /Users/roman.plevka/CascadeProjects
source aquavparku/bin/activate
pip install -r requirements.txt
```

### 2. Configure MQTT Settings

Set environment variables (recommended):

```bash
export SWIM_MQTT_BROKER="192.168.1.100"
export SWIM_MQTT_PORT="1883"
export SWIM_MQTT_USERNAME="your_mqtt_user"
export SWIM_MQTT_PASSWORD="your_mqtt_password"
export SWIM_MQTT_TOPIC_PREFIX="aquapark"
```

Or the script will use these defaults:
- `SWIM_MQTT_BROKER` → `homeassistant.local`
- `SWIM_MQTT_PORT` → `1883`
- `SWIM_MQTT_USERNAME` → `mqtt_user`
- `SWIM_MQTT_PASSWORD` → `mqtt_password`
- `SWIM_MQTT_TOPIC_PREFIX` → `aquapark`

### 3. Set Up Cron Job

The script handles the 9:00-20:30 time window internally, so you can run it every 5 minutes:

```bash
crontab -e
```

Add this line:

```cron
SWIM_MQTT_BROKER=192.168.1.100
SWIM_MQTT_USERNAME=your_mqtt_user
SWIM_MQTT_PASSWORD=your_mqtt_password
*/5 * * * * cd /Users/roman.plevka/CascadeProjects && source aquavparku/bin/activate && python aquapark_occupancy.py >> /tmp/aquapark.log 2>&1
```

**Note:** The script will exit immediately if run outside operating hours (9:00-20:30 Prague time).

### 4. Configure Home Assistant

Add the contents of `homeassistant_config.yaml` to your Home Assistant `configuration.yaml` file.

After adding the configuration:
1. Restart Home Assistant
2. The sensors will appear as:
   - `sensor.aquapark_swimming_pool`
   - `sensor.aquapark_fun_zone`
   - `sensor.aquapark_wellness`
   - `sensor.aquapark_exterior`

---

## Testing

Test the script manually:

```bash
cd /Users/roman.plevka/CascadeProjects
source aquavparku/bin/activate
python aquapark_occupancy.py
```

Expected output during operating hours:
```json
{
  "swimming": 0,
  "fun": 0,
  "wellness": 0,
  "exterior": 0
}
```

Expected output outside operating hours:
```json
{
  "status": "closed",
  "message": "Pool is closed (operating hours: 9:00-20:30 Prague time)",
  "current_time": "22:35"
}
```

## MQTT Topics

The script publishes to these topics:
- `aquapark/swimming`
- `aquapark/fun`
- `aquapark/wellness`
- `aquapark/exterior`

Each message contains:
```json
{
  "occupancy": 0,
  "timestamp": "2026-01-20T00:35:00.123456"
}
```

## Environment Variables

All configuration is done via environment variables with the `SWIM_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `SWIM_MQTT_BROKER` | `homeassistant.local` | MQTT broker hostname or IP |
| `SWIM_MQTT_PORT` | `1883` | MQTT broker port |
| `SWIM_MQTT_USERNAME` | `mqtt_user` | MQTT username |
| `SWIM_MQTT_PASSWORD` | `mqtt_password` | MQTT password |
| `SWIM_MQTT_TOPIC_PREFIX` | `aquapark` | MQTT topic prefix |

## Troubleshooting

### Docker
- **Container not starting**: Check logs with `docker logs aquapark-monitor`
- **No data in MQTT**: Verify network connectivity between containers
- **Check if script is running**: `docker exec aquapark-monitor cat /var/log/aquapark.log`

### Manual Installation
- **SSL Certificate Warnings**: These are suppressed in the script but are harmless
- **MQTT Connection Issues**: Check your broker IP, port, and credentials
- **No Data in Home Assistant**: Verify MQTT integration is configured and the broker is running
- **Script Not Running**: Check cron logs at `/tmp/aquapark.log`

### General
- **Script runs outside hours**: The script will exit immediately if run outside 9:00-20:30 Prague time
- **Timezone issues**: Ensure `TZ=Europe/Prague` is set (Docker) or system timezone is correct (manual)
