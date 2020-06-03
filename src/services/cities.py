class CitiesService:
    def __init__(self, connection):
        self.connection = connection

    def get_cities(self):
        cur = self.connection.execute(
            'SELECT * '
            'FROM city '
        )
        colors = cur.fetchall()
        return [dict(color) for color in colors]