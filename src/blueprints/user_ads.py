from flask import (
    Blueprint,
    jsonify,
)
from flask.views import MethodView

from database import db
from services.ads import AdsService


bp = Blueprint('user_ads', __name__)


class UserAdsView(MethodView):
    def get(self, user_id):
        with db.connection as con:
            service = AdsService(con)
            ads = service.get_ads(user_id=user_id)
            return jsonify(ads)


bp.add_url_rule('/<int:user_id>/ads', view_func=UserAdsView.as_view('user_ads'))