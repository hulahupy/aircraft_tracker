"""Аналитические запросы к данным воздушных судов в PostgreSQL."""

from aircraft_tracker.database import get_connection


class DBManager:
    """Предоставляет методы чтения и анализа таблиц проекта."""

    def get_countries_and_aeroplanes_count(self):
        """Возвращает список стран и число наблюдений самолётов в каждой."""
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT c.name, COUNT(a.id) AS aeroplanes_count
                    FROM countries AS c
                    LEFT JOIN aeroplanes AS a ON c.id = a.country_id
                    GROUP BY c.id, c.name
                    ORDER BY c.name;
                    """
                )
                return cursor.fetchall()

    def get_all_aeroplanes(self):
        """Возвращает все сохранённые наблюдения воздушных судов."""
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, icao24, callsign, country_id, longitude, latitude,
                        altitude, velocity, on_ground, last_contact, collected_at
                    FROM aeroplanes
                    ORDER BY collected_at DESC, id DESC;
                    """
                )
                return cursor.fetchall()

    def get_avg_speed(self):
        """Возвращает среднюю скорость в м/с по наблюдениям самолётов в воздухе."""
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT AVG(velocity)
                    FROM aeroplanes
                    WHERE velocity IS NOT NULL AND on_ground = FALSE;
                    """
                )
                return cursor.fetchone()[0]

    def get_aeroplanes_with_higher_speed(self):
        """Возвращает наблюдения самолётов со скоростью выше средней."""
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, icao24, callsign, country_id, longitude, latitude,
                        altitude, velocity, on_ground, last_contact, collected_at
                    FROM aeroplanes
                    WHERE on_ground = FALSE
                      AND velocity IS NOT NULL
                      AND velocity > (
                          SELECT AVG(velocity)
                          FROM aeroplanes
                          WHERE velocity IS NOT NULL AND on_ground = FALSE
                      )
                    ORDER BY velocity DESC;
                    """
                )
                return cursor.fetchall()

    def get_aeroplanes_with_keyword(self, keyword: str):
        """Ищет наблюдения по подстроке позывного без учёта регистра."""
        if not keyword or not keyword.strip():
            raise ValueError("Ключевое слово не должно быть пустым.")
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, icao24, callsign, country_id, longitude, latitude,
                        altitude, velocity, on_ground, last_contact, collected_at
                    FROM aeroplanes
                    WHERE callsign ILIKE %s
                    ORDER BY collected_at DESC, id DESC;
                    """,
                    (f"%{keyword.strip()}%",),
                )
                return cursor.fetchall()
