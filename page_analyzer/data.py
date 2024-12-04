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
            cur.execute("SELECT * FROM urls;")
            self.conn.commit()
            return [dict(row) for row in cur]
