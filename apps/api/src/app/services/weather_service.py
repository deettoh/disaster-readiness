"""Open-Meteo weather service for real-time precipitation data."""

import asyncio
import logging
from datetime import UTC, datetime

import httpx

from app.schemas.weather import RainfallReading, WeatherSnapshotResponse

logger = logging.getLogger(__name__)

# Petaling Jaya neighbourhood centroids (lat, lng) derived from pj_neighbourhood.geojson.
# Once grid_cells are seeded, will be replaced with dynamic DB centroid queries.
PJ_NEIGHBOURHOODS: dict[str, tuple[float, float]] = {
    "Petaling Jaya": (3.132644, 101.611261),
    "PJS 5": (3.076968, 101.622622),
    "Bandar Utama": (3.139609, 101.608388),
    "Damansara Perdana (PJU 8)": (3.168860, 101.607393),
    "PJS 8": (3.076816, 101.609548),
    "PJS 10": (3.075923, 101.605696),
    "SS 10": (3.082202, 101.614126),
    "PJS 6": (3.077775, 101.617488),
    "PJS 4": (3.073898, 101.628333),
    "PJS 3": (3.074230, 101.640789),
    "PJS 2": (3.079458, 101.633352),
    "PJS 1": (3.078690, 101.649962),
    "Seksyen 18": (3.081081, 101.657710),
    "SS 11": (3.088732, 101.596512),
    "SS 7": (3.098956, 101.597555),
    "SS 8": (3.087593, 101.611205),
    "SS 9A": (3.087517, 101.619666),
    "SS 6": (3.101403, 101.599103),
    "SS 5": (3.099823, 101.604657),
    "SS 4": (3.109816, 101.600965),
    "SS 3": (3.100569, 101.611896),
    "SS 1": (3.101872, 101.618279),
    "Seksyen 13": (3.114879, 101.637500),
    "Seksyen 1A": (3.085158, 101.655835),
    "Seksyen 5": (3.097125, 101.655574),
    "Seksyen 4": (3.090713, 101.643239),
    "Seksyen 3": (3.090046, 101.648323),
    "Seksyen 2": (3.084881, 101.642528),
    "Seksyen 1": (3.083990, 101.651100),
    "Seksyen 6": (3.092752, 101.651465),
    "SS 9": (3.085841, 101.617710),
    "Seksyen 51": (3.088565, 101.636123),
    "Seksyen 8": (3.099792, 101.638515),
    "Seksyen 7": (3.098134, 101.643623),
    "Seksyen 51A": (3.096780, 101.631630),
    "Seksyen 22": (3.101488, 101.624124),
    "Seksyen 52": (3.104826, 101.643519),
    "Seksyen 14": (3.103568, 101.631461),
    "Seksyen 12": (3.112295, 101.644478),
    "Seksyen 11": (3.109866, 101.646938),
    "Seksyen 10": (3.104518, 101.650272),
    "Seksyen 9": (3.101161, 101.650395),
    "Seksyen 20": (3.107758, 101.626232),
    "Seksyen 21": (3.110334, 101.622158),
    "Seksyen 16": (3.124700, 101.643835),
    "Seksyen 17A": (3.130416, 101.631566),
    "Seksyen 17": (3.123986, 101.632829),
    "Seksyen 19": (3.119738, 101.629124),
    "SS 2": (3.116268, 101.619046),
    "SS 25": (3.112950, 101.597933),
    "SS 24": (3.115533, 101.610135),
    "SS 23": (3.119610, 101.611816),
    "SS 22": (3.126745, 101.619852),
    "SS 22A": (3.129160, 101.614718),
    "SS 20": (3.137317, 101.626513),
    "SS 21": (3.138968, 101.619628),
    "SS 26": (3.120021, 101.606431),
    "PJU 6": (3.132956, 101.613697),
    "PJU 1": (3.117786, 101.597607),
    "PJU 1A": (3.115936, 101.580411),
    "PJU 2": (3.121067, 101.573849),
    "PJU 7": (3.159837, 101.613570),
    "PJU 9": (3.196403, 101.618216),
    "PJU 8": (3.172242, 101.616291),
    "PJU 10": (3.197174, 101.588261),
    "PJU 5": (3.171148, 101.580481),
    "PJU 4": (3.139742, 101.562018),
    "PJU 3": (3.141563, 101.580056),
}

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_TIMEOUT = 10.0  # seconds per request
BATCH_CONCURRENCY = 10  # max parallel requests


class OpenMeteoClient:
    """Async HTTP client for Open-Meteo current weather data."""

    def __init__(self, timeout: float = OPEN_METEO_TIMEOUT) -> None:
        """Initialize Open-Meteo client with configurable timeout."""
        self._timeout = timeout

    async def fetch_current(
        self,
        lat: float,
        lng: float,
        *,
        client: httpx.AsyncClient,
    ) -> dict:
        """Fetch current weather for a single coordinate.

        Returns raw JSON dict from Open-Meteo or empty dict on failure.
        """
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": "precipitation,temperature_2m,relative_humidity_2m,weather_code",
            "timezone": "Asia/Kuala_Lumpur",
        }
        try:
            resp = await client.get(
                OPEN_METEO_BASE,
                params=params,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, Exception) as exc:
            logger.warning(
                "Open-Meteo request failed for (%.4f, %.4f): %s", lat, lng, exc
            )
            return {}


class WeatherService:
    """Orchestrates rainfall data fetching across PJ neighbourhoods."""

    def __init__(self) -> None:
        """Initialize weather service with Open-Meteo client."""
        self._client = OpenMeteoClient()

    async def get_weather_snapshot(self) -> WeatherSnapshotResponse:
        """Fetch current precipitation for all PJ neighbourhoods."""
        semaphore = asyncio.Semaphore(BATCH_CONCURRENCY)
        readings: list[RainfallReading] = []

        async with httpx.AsyncClient() as http_client:

            async def _fetch_one(
                name: str, lat: float, lng: float
            ) -> RainfallReading | None:
                async with semaphore:
                    data = await self._client.fetch_current(
                        lat, lng, client=http_client
                    )
                if not data or "current" not in data:
                    return None

                current = data["current"]
                time_str = current.get("time", "")
                try:
                    ts = datetime.fromisoformat(time_str)
                except (ValueError, TypeError):
                    ts = datetime.now(tz=UTC)

                return RainfallReading(
                    neighbourhood=name,
                    lat=lat,
                    lng=lng,
                    precipitation_mm=current.get("precipitation", 0.0),
                    temperature_c=current.get("temperature_2m"),
                    relative_humidity=current.get("relative_humidity_2m"),
                    weather_code=current.get("weather_code"),
                    timestamp=ts,
                )

            tasks = [
                _fetch_one(name, lat, lng)
                for name, (lat, lng) in PJ_NEIGHBOURHOODS.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, RainfallReading):
                readings.append(result)
            elif isinstance(result, Exception):
                logger.warning("Neighbourhood fetch error: %s", result)

        return WeatherSnapshotResponse(
            readings=readings,
            fetched_at=datetime.now(tz=UTC),
        )
