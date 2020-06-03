import os
import uuid

from flask import (
    Blueprint,
    current_app,
    request,
    send_from_directory,
    url_for,
)
from flask.views import MethodView

from auth import auth_required

bp = Blueprint('images', __name__)


class ImageView(MethodView):
    def get(self, image_name):
        upload_dir = current_app.config['UPLOAD_DIR']
        return send_from_directory(upload_dir, image_name)


class ImagesView(MethodView):
    @auth_required
    def post(self, user):
        file = request.files['image']
        if not user['is_seller']:
            return 'Нужно быть продавцом', 403
        if file:
            upload_dir = current_app.config['UPLOAD_DIR']
            filename = f'{uuid.uuid4()}{os.path.splitext(file.filename)[1]}'
            file.save(os.path.join(upload_dir, filename))
            return {
                'url': url_for('images.image', image_name=filename)
            }, 200
        return 'Вы не прикрепили картинку', 403


bp.add_url_rule('', view_func=ImagesView.as_view('images'))
bp.add_url_rule('/<image_name>', view_func=ImageView.as_view('image'))


