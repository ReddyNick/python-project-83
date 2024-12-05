from psycopg2.extras import DictCursor
from datetime import datetime


class UrlRepository:
    def __init__(self, conn):
        self.conn = conn

    def save(self, name):
        timestampt = datetime.now().replace(microsecond=0)
        url_data = {'name': name, 'created_at': timestampt}
        with self.conn.cursor() as cur:
            sql = """
            INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;
            """
            cur.execute(sql, (url_data['name'], url_data['created_at']))
            url_data['id'] = cur.fetchone()[0]
            self.conn.commit()
        return url_data

    def find(self, id):
        return self._find_by('id', id)

    def find_by_name(self, name):
        return self._find_by('name', name)

    def _find_by(self, property_name, value):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f"SELECT * FROM urls WHERE {property_name} = %s",
                        (value,))
            row = cur.fetchone()
            self.conn.commit()
        return dict(row) if row else None

    def get_list(self):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                WITH last_checks AS (
                    SELECT a.* FROM url_checks as a
                    INNER JOIN (
                        SELECT MAX(id) as max_id FROM url_checks
                        GROUP BY url_id
                    ) as b
                    ON a.id = b.max_id
                )
                SELECT
                    urls.*,
                    last_checks.created_at as last_check_time,
                    last_checks.status_code
                FROM urls
                LEFT JOIN last_checks
                ON urls.id = last_checks.url_id
                ORDER BY urls.id DESC;
                """)
            self.conn.commit()
            return [dict(row) for row in cur]

    def save_check(self, check_info):
        timestampt = datetime.now().replace(microsecond=0)
        check_info['created_at'] = timestampt
        with self.conn.cursor() as cur:
            sql = """
            INSERT INTO url_checks (url_id, status_code, created_at)
            VALUES (%s, %s, %s) RETURNING id;
            """
            cur.execute(sql, (
                check_info['url_id'],
                check_info['status_code'],
                check_info['created_at'],
                ))
            check_info['id'] = cur.fetchone()[0]
            self.conn.commit()

        return check_info

    def get_all_checks(self, id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM url_checks
                WHERE url_id = %s ORDER BY created_at DESC;
                """, (id,))
            self.conn.commit()
            return [dict(row) for row in cur]
