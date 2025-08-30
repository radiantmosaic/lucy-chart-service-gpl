# Lucy Bot Chart Service (GPL)

A microservice for generating astrological charts using the Kerykeion library. This service is licensed under GPL v3+ to comply with Kerykeion's licensing requirements.

## Overview

This chart generation service provides an HTTP API for creating natal charts, synastry charts, and transit charts. It's designed as a standalone microservice that can be used by any application requiring astrological chart generation.

## Features

- **Natal Charts**: Generate birth charts with full astrological aspects and house systems
- **Synastry Charts**: Compare two birth charts for relationship analysis  
- **Transit Charts**: Generate date-only planetary position charts with no time or location requirements
- **Rulership Systems**: Support for both traditional (7 classical planets) and modern (including outer planets and nodes) rulership
- **Multiple House Systems**: Placidus, Whole Sign, Campanus
- **Multiple Zodiac Systems**: Tropical and Lahiri Vedic/Sidereal
- **HTTP API**: RESTful endpoints for easy integration
- **Docker Support**: Containerized deployment

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status.

### Generate Chart
```
POST /generate-chart
Content-Type: application/json
```

Request body should contain chart generation parameters. See the source code for detailed parameter specifications.

## Installation

### Docker (Recommended)
```bash
# Build the image
docker build -t chart-service .

# Run the service
docker run -p 5000:5000 chart-service

# Health check
curl http://localhost:5000/health
```

### Docker Compose (Production)
```yaml
services:
  chart-service:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SWISSEPH_PATH=/usr/share/swisseph
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python chart_service.py

# Service will be available at http://localhost:5000
```

## Usage Examples

### Generate a Natal Chart
```bash
curl -X POST http://localhost:5000/generate-chart \
  -H "Content-Type: application/json" \
  -d '{
    "chart_data": {
      "name": "John Doe",
      "birth_date": "1990-01-01",
      "birth_time": "12:00:00",
      "birth_city": "London",
      "birth_country": "GB",
      "birth_latitude": 51.5074,
      "birth_longitude": -0.1278
    },
    "user_preferences": {
      "houseSystem": "placidus",
      "zodiac": "tropical",
      "rulership": "modern"
    }
  }'
```

### Generate a Transit Chart
Transit charts show pure planetary positions without location-dependent houses or angles. They only require a date and automatically use noon UTC at Greenwich for consistent planetary positions.

```bash
curl -X POST http://localhost:5000/generate-chart \
  -H "Content-Type: application/json" \
  -d '{
    "chart_data": {
      "name": "Transit Chart",
      "birth_date": "2024-01-01"
    },
    "is_transit": true,
    "user_preferences": {
      "zodiac": "tropical",
      "rulership": "modern"
    }
  }'
```

**Transit Chart Features:**
- **Date Only**: No time or location required
- **No House Divisions**: No cusps or house systems displayed
- **No Location-Dependent Angles**: Excludes Ascendant and Midheaven  
- **Pure Planetary Positions**: Shows only planets in zodiacal degrees
- **Consistent Reference**: Always uses noon UTC at Greenwich
- **Perfect For**: Tracking current planetary weather and aspects

## Configuration Options

### User Preferences

The `user_preferences` object supports the following options:

#### House System (`houseSystem`)
- `"placidus"` (default) - Placidus house system
- `"whole-sign"` - Whole Sign house system  
- `"campanus"` - Campanus house system

#### Zodiac System (`zodiac`)
- `"tropical"` (default) - Tropical zodiac
- `"lahiri-vedic"` - Lahiri (Chitrapaksha) Vedic/Sidereal zodiac

#### Rulership System (`rulership`)
- `"modern"` (default) - Modern rulership with all planets
  - Includes: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, North Node
  - Shows outer planets and lunar nodes
- `"traditional"` - Traditional/Classical rulership  
  - Includes: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn
  - Excludes outer planets (Uranus, Neptune, Pluto) and nodes
  - Uses only the 7 classical planets known to ancient astrologers

### Example with Traditional Rulership
```bash
curl -X POST http://localhost:5000/generate-chart \
  -H "Content-Type: application/json" \
  -d '{
    "chart_data": {
      "name": "Classical Chart",
      "birth_date": "1990-01-01",
      "birth_time": "12:00:00",
      "birth_city": "London",
      "birth_country": "GB"
    },
    "user_preferences": {
      "houseSystem": "whole-sign",
      "zodiac": "tropical",
      "rulership": "traditional"
    }
  }'
```

## Dependencies

- **Kerykeion**: Astrological calculations and chart generation
- **Flask**: HTTP web framework
- **Python 3.12+**: Runtime environment

## Licensing

This project is licensed under GNU General Public License v3 or later (GPL-3.0+) to comply with the licensing requirements of the Kerykeion library.

### Why GPL?

The Kerykeion library is licensed under GPL v3+, which requires derivative works to also be licensed under GPL. This chart service uses Kerykeion for astrological calculations, making it a derivative work that must comply with GPL requirements.

### Compliance Notes

- All source code is available in this repository
- Users have the right to modify and redistribute under GPL terms
- Any applications using this service must comply with GPL requirements for their chart generation components
- This service can be used via HTTP API to maintain licensing separation from proprietary codebases

## Contributing

Contributions are welcome! Please ensure all contributions comply with GPL v3+ licensing.

## Support

This is a GPL-licensed microservice extracted from the Lucy Bot project for compliance with Kerykeion's licensing requirements.