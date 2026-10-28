"""Unit-тесты вспомогательной логики API-клиента."""

from aircraft_tracker.api_client import APIClient


class FakeResponse:
    """Минимальная имитация requests.Response."""

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        """Имитирует успешный HTTP-ответ."""

    def json(self):
        """Возвращает тестовый JSON."""
        return self.payload


class FakeSession:
    """Имитация HTTP-сессии для тестирования без сети."""

    def __init__(self, payload):
        self.payload = payload
        self.headers = {}

    def get(self, *args, **kwargs):
        """Возвращает заранее подготовленный ответ."""
        return FakeResponse(self.payload)


def test_get_country_bounds_parses_bounding_box():
    """Проверяет преобразование bounding box в числовые границы."""
    client = APIClient(
        session=FakeSession(
            [{"boundingbox": ["41.3", "51.1", "-5.2", "9.6"]}]
        )
    )
    result = client.get_country_bounds("France", "fr")

    assert result["country_code"] == "FR"
    assert result["lat_min"] == 41.3
    assert result["lat_max"] == 51.1
    assert result["lon_min"] == -5.2
    assert result["lon_max"] == 9.6


def test_get_country_bounds_raises_if_not_found():
    """Проверяет понятную ошибку, если Nominatim не нашёл страну."""
    client = APIClient(session=FakeSession([]))

    try:
        client.get_country_bounds("Unknown", "zz")
    except ValueError as error:
        assert "Не найдена страна" in str(error)
    else:
        raise AssertionError("Ожидался ValueError")
