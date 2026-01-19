#!/usr/bin/env python3
"""
Script to parse current occupancy percentages from www.aquavparku.cz
Publishes to MQTT for Home Assistant integration
Only runs between 9:00 and 20:30 Prague time
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import os
from datetime import datetime, time
import pytz
import paho.mqtt.client as mqtt
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# MQTT Configuration - sourced from environment variables with SWIM_ prefix or defaults
MQTT_BROKER = os.getenv("SWIM_MQTT_BROKER", "homeassistant.local")
MQTT_PORT = int(os.getenv("SWIM_MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("SWIM_MQTT_USERNAME", "mqtt_user")
MQTT_PASSWORD = os.getenv("SWIM_MQTT_PASSWORD", "mqtt_password")
MQTT_TOPIC_PREFIX = os.getenv("SWIM_MQTT_TOPIC_PREFIX", "aquapark")

def is_within_operating_hours():
    """Check if current time is between 9:00 and 20:30 Prague time"""
    prague_tz = pytz.timezone('Europe/Prague')
    now = datetime.now(prague_tz)
    current_time = now.time()
    
    start_time = time(9, 0)
    end_time = time(20, 30)
    
    return start_time <= current_time <= end_time

def fetch_occupancy_data():
    """Fetch and parse occupancy data from aquavparku.cz"""
    url = "https://www.aquavparku.cz/oteviraci-doba-arealu-a-aktualni-obsazenost"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        zone_patterns = [
            ("swimming", r"Zóna 1:\s*Plavecký bazénaktuálně:\s*(\d+)\s*%"),
            ("fun", r"Zóna 2:\s*Relaxační a zábavní zónaaktuálně:\s*(\d+)\s*%"),
            ("wellness", r"Zóna 3:\s*Wellnessaktuálně:\s*(\d+)\s*%"),
            ("exterior", r"Zóna 4:\s*Letní areálaktuálně:\s*(\d+)\s*%")
        ]
        
        page_text = soup.get_text()
        
        occupancy_data = {}
        for zone_name, pattern in zone_patterns:
            match = re.search(pattern, page_text)
            if match:
                occupancy_data[zone_name] = int(match.group(1))
            else:
                occupancy_data[zone_name] = None
        
        return occupancy_data
        
    except Exception as e:
        return {"error": str(e)}

def publish_to_mqtt(data):
    """Publish occupancy data to MQTT"""
    try:
        client = mqtt.Client()
        
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Publish each sensor individually
        for zone, occupancy in data.items():
            if zone != "error" and occupancy is not None:
                topic = f"{MQTT_TOPIC_PREFIX}/{zone}"
                payload = json.dumps({
                    "occupancy": occupancy,
                    "timestamp": datetime.now().isoformat()
                })
                client.publish(topic, payload, retain=True)
        
        client.disconnect()
        return True
        
    except Exception as e:
        print(json.dumps({"error": f"MQTT publish failed: {str(e)}"}), file=sys.stderr)
        return False

def main():
    """Main function to run the occupancy parser"""
    
    # Check if within operating hours
    if not is_within_operating_hours():
        prague_tz = pytz.timezone('Europe/Prague')
        now = datetime.now(prague_tz)
        print(json.dumps({
            "status": "closed",
            "message": "Pool is closed (operating hours: 9:00-20:30 Prague time)",
            "current_time": now.strftime("%H:%M")
        }))
        sys.exit(0)
    
    # Fetch data
    data = fetch_occupancy_data()
    
    # Publish to MQTT
    if "error" not in data:
        publish_to_mqtt(data)
    
    # Also print JSON for debugging
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
