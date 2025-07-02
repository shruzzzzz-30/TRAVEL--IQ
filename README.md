# 🌍 Travel IQ – Python-Based Travel Assistant (No Database)

**Travel IQ** is a lightweight Python application designed to assist travelers with real-time information using public APIs. No data is stored — all info is fetched live.

## ✨ Features
- 🌦️ Get real-time weather updates for any city
- 📍 Find top attractions in a given location
- ✈️ Access basic travel recommendations through APIs
- 🧠 Minimal and fast: No database, no signup, no storage

## 🧪 Tech Stack
- **Language:** Python
- **Framework:** Flask (for optional web interface)
- **APIs Used:**
  - OpenWeatherMap API (weather data)
  - Google Places API or similar (attractions & location info)

## 🔐 API Key Management
- API keys are securely managed using `.env` files
- Example:
```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
