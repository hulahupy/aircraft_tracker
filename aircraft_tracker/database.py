"""Подключение к PostgreSQL, создание схемы и сохранение данных."""

import os
from pathlib import Path
from typing import Any, Iterable

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Открывает новое подключение к PostgreSQL из переменных окружения."""
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "Не задан DB_PASSWORD. Скопируйте .env.example в .env и настройте подключение."
        )
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "aircraft_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=password,
    )


def create_tables() -> None:
    """Создаёт таблицы и индексы из файла schema.sql."""
    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)


def save_country_and_aeroplanes(
    bounds: dict[str, Any], states: Iterable[list[Any]]
) -> int:
    """Сохраняет страну и её наблюдения; возвращает число вставленных наблюдений."""
    inserted = 0
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO countries (
                    name, country_code, lat_min, lat_max, lon_min, lon_max
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (country_code)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    lat_min = EXCLUDED.lat_min,
                    lat_max = EXCLUDED.lat_max,
                    lon_min = EXCLUDED.lon_min,
                    lon_max = EXCLUDED.lon_max
                RETURNING id
                """,
                (
                    bounds["name"],
                    bounds["country_code"],
                    bounds["lat_min"],
                    bounds["lat_max"],
                    bounds["lon_min"],
                    bounds["lon_max"],
                ),
            )
            country_id = cursor.fetchone()[0]

            for state in states:
                # OpenSky StateVector indices: 0=icao24, 1=callsign,
                # 4=last_contact, 5=longitude, 6=latitude, 8=on_ground,
                # 9=velocity, 13=geo_altitude.
                if len(state) <= 13 or state[5] is None or state[6] is None:
                    continue
                callsign = state[1].strip() if state[1] else None
                cursor.execute(
                    """
                    INSERT INTO aeroplanes (
                        icao24, country_id, callsign, longitude, latitude,
                        altitude, velocity, on_ground, last_contact
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        state[0],
                        country_id,
                        callsign or None,
                        state[5],
                        state[6],
                        state[13],
                        state[9],
                        state[8],
                        state[4],
                    ),
                )
                inserted += 1
    return inserted
