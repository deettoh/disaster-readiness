"""Weather snapshot schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RainfallReading(BaseModel):
    """Single neighbourhood weather reading from Open-Meteo."""

    neighbourhood: str
    lat: float
    lng: float
    precipitation_mm: float
    temperature_c: float | None = None
    relative_humidity: float | None = None
    weather_code: int | None = None
    timestamp: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "neighbourhood": "PJU 5",
                "lat": 3.1711,
                "lng": 101.5805,
                "precipitation_mm": 2.4,
                "temperature_c": 29.1,
                "relative_humidity": 78.0,
                "weather_code": 61,
                "timestamp": "2026-03-06T16:00:00+08:00",
            }
        }
    )


class WeatherSnapshotResponse(BaseModel):
    """Collection of rainfall readings across PJ neighbourhoods."""

    readings: list[RainfallReading]
    fetched_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "readings": [
                    {
                        "neighbourhood": "PJU 5",
                        "lat": 3.1711,
                        "lng": 101.5805,
                        "precipitation_mm": 2.4,
                        "temperature_c": 29.1,
                        "relative_humidity": 78.0,
                        "weather_code": 61,
                        "timestamp": "2026-03-06T16:00:00+08:00",
                    }
                ],
                "fetched_at": "2026-03-06T16:05:00+08:00",
            }
        }
    )
