from flask import jsonify

from auth import auth_required


class ColorsService:
    def __init__(self, connection):
        self.connection = connection

    @auth_required
    def get_colors(self, user):
        if not user['is_seller']:
            return 'Нужно быть продавцом', 403

        cur = self.connection.execute(
            'SELECT * '
            'FROM color '
        )
        colors = cur.fetchall()
        return jsonify([dict(color) for color in colors])