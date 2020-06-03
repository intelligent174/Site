from flask import (
    Blueprint,
    request,
    jsonify,
)
from flask.views import MethodView

from database import db
from services.cities import CitiesService

bp = Blueprint('cities', __name__)


class CitiesView(MethodView):
    def get(self):
        with db.connection as con:
            service = CitiesService(con)
            cities = service.get_cities()
            return jsonify(cities)

    def post(self):
        request_json = request.json
        name = request_json.get('name')

        if not name:
            return '', 400

        with db.connection as con:
            try:
                cur = con.execute(
                    'SELECT * '
                    'FROM city '
                    'WHERE name = ? ',
                    (name,),
                )
                city = cur.fetchone()

                return jsonify(dict(city)), 200

            except:
                con.execute(
                    'INSERT INTO city (name) '
                    'VALUES (?) ',
                    (name,),
                )
                return '', 200


bp.add_url_rule('', view_func=CitiesView.as_view('cities'))