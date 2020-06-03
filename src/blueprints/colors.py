from flask import (
    Blueprint,
    request,
    jsonify,
)
from flask.views import MethodView

from auth import auth_required
from database import db
from services.colors import ColorsService

bp = Blueprint('colors', __name__)


class ColorsView(MethodView):
    def get(self):
        with db.connection as con:
            service = ColorsService(con)
            colors = service.get_colors()
            return colors

    @auth_required
    def post(self, user):
        if not user['is_seller']:
            return 'Нужно быть продавцом', 403

        request_json = request.json
        name = request_json.get('name')
        hex = request_json.get('hex')

        if not name or not hex:
            return '', 400

        with db.connection as con:
            try:
                cur = con.execute(
                    'SELECT * '
                    'FROM color '
                    'WHERE name = ? ',
                    (name,),
                )
                color = cur.fetchone()

                return jsonify(dict(color)), 200

            except:
                con.execute(
                    'INSERT INTO color (name, hex) '
                    'VALUES (?, ?) ',
                    (name, hex),
                )
                return '', 200


bp.add_url_rule('', view_func=ColorsView.as_view('colors'))
