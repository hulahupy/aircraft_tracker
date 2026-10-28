"""Точка входа приложения Aircraft Tracker."""

import os
import sys

import requests
from dotenv import load_dotenv

from aircraft_tracker.api_client import APIClient
from aircraft_tracker.config import COUNTRIES
from aircraft_tracker.database import (
    create_tables,
    get_connection,
    save_country_and_aeroplanes,
)
from aircraft_tracker.db_manager import DBManager


def main() -> None:
    """Создаёт схему, собирает данные и демонстрирует аналитические методы."""
    load_dotenv()
    try:
        create_tables()
        client = APIClient(
            client_id=os.getenv("OPENSKY_CLIENT_ID") or None,
            client_secret=os.getenv("OPENSKY_CLIENT_SECRET") or None,
        )
        manager = DBManager()

        for country_name, country_code in COUNTRIES:
            print(f"\nПолучение данных: {country_name}...")
            bounds = client.get_country_bounds(country_name, country_code)
            states = client.get_aeroplanes(bounds)
            inserted = save_country_and_aeroplanes(bounds, states)
            print(
                f"{country_name}: API вернуло {len(states)} состояний; "
                f"сохранено наблюдений с координатами: {inserted}"
            )

        print("\nСтраны и количество наблюдений:")
        for country, count in manager.get_countries_and_aeroplanes_count():
            print(f"- {country}: {count}")

        avg_speed = manager.get_avg_speed()
        if avg_speed is None:
            print("\nСредняя скорость: нет данных о скорости воздушных судов.")
        else:
            print(f"\nСредняя скорость: {avg_speed:.2f} м/с")

        print("\nПервые 10 наблюдений быстрее средней скорости:")
        for row in manager.get_aeroplanes_with_higher_speed()[:10]:
            print(row)

        print("\nПоследние наблюдения с позывным, содержащим ACA:")
        for row in manager.get_aeroplanes_with_keyword("ACA")[:10]:
            print(row)

    except requests.HTTPError as error:
        print(f"Ошибка HTTP при запросе к API: {error}", file=sys.stderr)
        if error.response is not None:
            print(f"Ответ сервера: {error.response.text[:500]}", file=sys.stderr)
        raise
    except (requests.RequestException, RuntimeError, ValueError) as error:
        print(f"Ошибка выполнения проекта: {error}", file=sys.stderr)
        raise
    except Exception as error:
        print(f"Непредвиденная ошибка: {error}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
