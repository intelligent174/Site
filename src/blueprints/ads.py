from flask import (
    Blueprint,
    jsonify,
    request,
)
from datetime import datetime

from flask.views import MethodView

from auth import auth_required
from database import db
from services.ads import (
    AdDoesNotExistError,
    AdsService,
)


bp = Blueprint('ads', __name__)


class AdsView(MethodView):
    def get(self):
        with db.connection as con:
            service = AdsService(con)
            ads = service.get_ads()
            return jsonify(ads)

    @auth_required
    def post(self, user):
        if not user['is_seller']:
            return 'Нужно быть продавцом', 403
        request_json = request.json
        title = request_json.pop('title', None)
        tags = request_json.pop('tags', None)
        tags_to_insert = [(tag,) for tag in tags]
        car = request_json.pop('car', None)
        images = car.pop('images', None)
        images = [(value['title'], value['url']) for value in images]
        colors = car.pop('colors', None)
        placeholders_tags = ', '.join('?' for _ in tags)

        with db.connection as con:
            con.executemany(
                'INSERT OR IGNORE INTO tag (name) '
                'VALUES (?) ',
                tags_to_insert,
            )

            cur = con.execute(
                'SELECT id '
                'FROM tag '
                f'WHERE name IN ({placeholders_tags}) ',
                tags,
            )
            rows = cur.fetchall()
            tags_id = [dict(row) for row in rows]

            cur = con.execute(
                'INSERT INTO car (make, model, mileage, num_owners, reg_number) '
                'VALUES (?, ?, ?, ?, ?) ',
                (car['make'], car['model'], car['mileage'], car['num_owners'], car['reg_number'],),
            )

            car_id = cur.lastrowid

            images = [(*value, car_id) for value in images]
            con.executemany(
                'INSERT INTO image (title, url, car_id) '
                'VALUES (?, ?, ?) ',
                (*images,),
            )

            current_datetime = datetime.now()

            cur = con.execute(
                'INSERT INTO ad (title, date, seller_id, car_id) '
                'VALUES (?, ?, ?, ?) ',
                (title, current_datetime, user['seller_id'], car_id,)
            )

            ad_id = cur.lastrowid
            tags_id_ad = [(tag['id'], ad_id) for tag in tags_id]

            con.executemany(
                'INSERT INTO adtag (tag_id, ad_id) '
                'VALUES (?, ?) ',
                tags_id_ad,
            )
            color = [(col, car_id) for col in colors]

            con.executemany(
                'INSERT OR IGNORE INTO carcolor(color_id, car_id) '
                'VALUES (?, ?) ',
                (*color,),
            )
        return 'Вы добавили объявление', 200


class AdView(MethodView):
    def get(self, ad_id):
        with db.connection as con:
            service = AdsService(con)
            try:
                ad = service.get_ad(ad_id)
            except AdDoesNotExistError:
                return '', 404
            else:
                return ad

    @auth_required
    def patch(self, user, ad_id):
        if not user['is_seller']:
            return 'Нужно быть продавцом', 403
        seller_id = user['seller_id']

        with db.connection as con:
            cur = con.execute(
                'SELECT COUNT(ad.id) AS count_id '
                'FROM ad '
                f'WHERE seller_id = {seller_id} '
                f'AND ad.id = {ad_id} ',
            )
            ad_current_user = dict(cur.fetchone())

        if not ad_current_user['count_id']:
            return 'Вы можете редактировать только свои объявлния', 403

        request_json = dict(request.json)
        title = request_json.pop('title', None)
        tags = request_json.pop('tags', None)
        tags_to_insert = [(tag,) for tag in tags]
        car = request_json.pop('car', {})
        colors = car.pop('colors', None)
        images = car.pop('images', None)

        car_params = ','.join(f'{key} = ?' for key in car)

        query_car = f'UPDATE car SET {car_params} WHERE id = ?'
        placeholders_tags = ', '.join('?' for _ in tags)

        with db.connection as con:
            cur = con.execute(
                'SELECT adtag.id AS id_adtag '
                'FROM tag '
                '     JOIN adtag ON tag.id = adtag.tag_id '
                '     JOIN ad ON adtag.ad_id = ad.id '
                f'WHERE ad.id = ? ',
                (ad_id,),
            )
            rows = cur.fetchall()
            adtag_id = [row['id_adtag'] for row in rows]
            ready_adtags_id = [(tag,) for tag in adtag_id]

            con.executemany(
                'DELETE '
                'FROM adtag '
                'WHERE id = ? ',
                ready_adtags_id,
            )

            con.executemany(
                'INSERT OR IGNORE INTO tag (name) '
                'VALUES (?) ',
                tags_to_insert,
            )

            cur = con.execute(
                'SELECT id '
                'FROM tag '
                f'WHERE name IN ({placeholders_tags}) ',
                tags,
            )
            rows = cur.fetchall()
            id_tags = [dict(row) for row in rows]

            tags_id_ad = [(tag['id'], ad_id) for tag in id_tags]

            con.executemany(
                ' INSERT INTO adtag (tag_id, ad_id) '
                ' VALUES (?, ?) ',
                tags_id_ad,

            )

            cur = con.execute(
                'SELECT car_id '
                'FROM ad '
                'WHERE id = ? ',
                (ad_id,),
            )
            car_id = dict(cur.fetchone())

            con.execute(query_car, (*car.values(), car_id['car_id'],))

            cur = con.execute(
                'SELECT id '
                'FROM image '
                'WHERE car_id = ? ',
                (car_id['car_id'],),
            )

            images_id = cur.fetchall()
            image_id = [dict(image) for image in images_id]
            image_id_to_delete = [(_['id'],) for _ in image_id]
            print(image_id_to_delete)

            con.executemany(
                'DELETE '
                'FROM image '
                'WHERE id = ? ',
                image_id_to_delete,
            )

            images_data = [(image['title'], image['url'], car_id['car_id']) for image in images]
            print(images_data)
            con.executemany(
                'INSERT INTO image (title, url, car_id) '
                'VALUES (?, ?, ?) ',
                images_data,
            )

            con.execute(
                'UPDATE ad '
                'SET title = ? '
                'WHERE id = ? ',
                (title, ad_id,),
            )

            colors_data = [(col_id, car_id['car_id']) for col_id in colors]

            con.executemany(
                'UPDATE carcolor '
                'SET color_id = ? '
                'WHERE car_id = ? ',
                colors_data,
            )

        return 'Объявление отредактировано', 200

    @auth_required
    def delete(self, user, ad_id):
        if not user['is_seller']:
            return 'Нужно быть продавцом', 403
        seller_id = user['seller_id']

        with db.connection as con:
            cur = con.execute(
                'SELECT COUNT(ad.id) AS count_id '
                'FROM ad '
                'WHERE seller_id = ? '
                'AND ad.id = ? ',
                (seller_id, ad_id,),
            )
            ad_current_user = dict(cur.fetchone())
        if not ad_current_user['count_id']:
            return 'Вы можете удалять только свои объявления', 403
        return 'Вы удалили объявление ', 200


bp.add_url_rule('', view_func=AdsView.as_view('ads'))
bp.add_url_rule('/<int:ad_id>', view_func=AdView.as_view('ad'))
