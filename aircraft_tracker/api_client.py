"""Клиент для получения географических границ и состояний самолётов."""

import time
from typing import Any

import requests

from aircraft_tracker.config import (
    NOMINATIM_DELAY_SECONDS,
    NOMINATIM_USER_AGENT,
    OPENSKY_TIMEOUT,
    REQUEST_TIMEOUT,
)


class APIClient:
    """Выполняет HTTP-запросы к Nominatim и OpenSky."""

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OPENSKY_URL = "https://opensky-network.org/api/states/all"
    TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Инициализирует HTTP-сессию и необязательные OAuth2-данные."""
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": NOMINATIM_USER_AGENT})
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: str | None = None

    def _get_access_token(self) -> str | None:
        """Получает OAuth2-токен OpenSky, если заданы учётные данные."""
        if not self.client_id or not self.client_secret:
            return None
        response = self.session.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise RuntimeError("OpenSky не вернул access_token.")
        self._access_token = token
        return token

    def get_country_bounds(self, country_name: str, country_code: str) -> dict[str, Any]:
        """Возвращает bounding box страны из Nominatim."""
        response = self.session.get(
            self.NOMINATIM_URL,
            params={
                "country": country_name,
                "countrycodes": country_code.lower(),
                "featureType": "country",
                "format": "jsonv2",
                "limit": 1,
            },
            headers={
                "User-Agent": NOMINATIM_USER_AGENT,
                "Accept": "application/json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ValueError(f"Не найдена страна: {country_name} ({country_code})")

        # Nominatim: [south, north, west, east]
        bounds = results[0]["boundingbox"]
        return {
            "name": country_name,
            "country_code": country_code.upper(),
            "lat_min": float(bounds[0]),
            "lat_max": float(bounds[1]),
            "lon_min": float(bounds[2]),
            "lon_max": float(bounds[3]),
        }

    def get_aeroplanes(self, bounds: dict[str, Any]) -> list[list[Any]]:
        """Возвращает состояния воздушных судов внутри bounding box."""
        headers = {}
        if self.client_id and self.client_secret:
            token = self._access_token or self._get_access_token()
            headers["Authorization"] = f"Bearer {token}"

        response = self.session.get(
            self.OPENSKY_URL,
            params={
                "lamin": bounds["lat_min"],
                "lamax": bounds["lat_max"],
                "lomin": bounds["lon_min"],
                "lomax": bounds["lon_max"],
            },
            headers=headers,
            timeout=OPENSKY_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("states") or []

    def get_all_country_data(
        self, countries: list[tuple[str, str]]
    ) -> list[tuple[dict[str, Any], list[list[Any]]]]:
        """Получает границы и наблюдения самолётов для списка стран."""
        result = []
        for index, (name, code) in enumerate(countries):
            bounds = self.get_country_bounds(name, code)
            states = self.get_aeroplanes(bounds)
            result.append((bounds, states))
            # Пауза ограничивает частоту запросов к публичному Nominatim.
            if index < len(countries) - 1:
                time.sleep(NOMINATIM_DELAY_SECONDS)
        return result
