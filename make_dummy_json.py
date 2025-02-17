#!/usr/bin/env python3

# This script creates a dummy json file for testing the Price Control program
# Run it, enter a date to fake and rename the file to your area (SE3 is default)
# Then put the file in the 'log' directory

import json
import math
from datetime import datetime, timedelta

# Constants
EXR = 11.0  # Set exchange rate
AMP = 1.5   # Amplitude of sine wave
BASE = 2.0  # Base value for SEK_per_kWh
PERIODS = 96  # 96 intervals (15 minutes each in 24 hours)

# Prompt user for date
date_str = input("Enter the date (YYYY-MM-DD): ")
try:
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
except ValueError:
    print("Invalid date format.")
    exit(1)

# Generate data
entries = []
for i in range(PERIODS):
    time_start = base_date + timedelta(minutes=15 * i)
    time_end = time_start + timedelta(minutes=15)
    
    sek_per_kwh = BASE + AMP * math.sin(2 * math.pi * i / PERIODS)
    eur_per_kwh = sek_per_kwh / EXR
    
    entry = {
        "SEK_per_kWh": round(sek_per_kwh, 5),
        "EUR_per_kWh": round(eur_per_kwh, 5),
        "EXR": EXR,
        "time_start": time_start.isoformat() + "+01:00",
        "time_end": time_end.isoformat() + "+01:00"
    }
    entries.append(entry)

# Save to JSON file
filename = f"{date_str}_SE3.json"
with open(filename, "w") as f:
    json.dump(entries, f, indent=4)

print(f"JSON file '{filename}' generated successfully.")
