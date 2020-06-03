import sqlite3

from flask import (
    Blueprint,
    jsonify,
    request,
)
from flask.views import MethodView
from werkzeug.security import generate_password_hash

from auth import auth_required
from database import db


bp = Blueprint('users', __name__)


class UsersView(MethodView):
    def get(self):
        with db.connection as con:
            cur = con.execute(
                'SELECT id, first_name, last_name, email '
                'FROM account '
            )
            rows = cur.fetchall()
        return jsonify([dict(row) for row in rows])

    def post(self):
        request_json = request.json
        email = request_json.get('email')
        password = request_json.get('password')
        first_name = request_json.get('first_name')
        last_name = request_json.get('last_name')
        is_seller = request_json.get('is_seller')
        phone = request_json.get('phone')
        zip_code = request_json.get('zip_code')
        city_id = request_json.get('city_id')
        street = request_json.get('street')
        home = request_json.get('home')

        list_fields = (email, password, first_name, last_name,)

        if not all(list_fields):
            return 'Вы заполнили не все поля', 401

        password_hash = generate_password_hash(password)

        if not is_seller:
            with db.connection as con:
                try:
                    con.execute(
                        'INSERT INTO account (email, password, first_name, last_name ) '
                        'VALUES (?, ?, ?, ? ) ',
                        (email, password_hash, first_name, last_name),
                    )
                    cur = con.execute(
                        'SELECT account.id, '
                        '       email, '
                        '       first_name, '
                        '       last_name, '
                        '       (seller.id IS NOT NULL) AS is_seller '
                        'FROM account  '
                        'LEFT JOIN seller ON seller.account_id = account.id '
                        'WHERE email = ? ',
                        (email,),
                    )
                    user = cur.fetchone()

                except sqlite3.IntegrityError:
                    return 'Поле email должен быть уникальным', 409
            return jsonify(dict(user)), 201

        else:
            list_fields += (phone, zip_code, city_id, street, home,)

            if not all(list_fields):
                return 'Вы заполнили не все поля', 401

            with db.connection as con:
                try:
                    con.execute(
                        'INSERT INTO account (email, password, first_name, last_name ) '
                        'VALUES (?, ?, ?, ? ) ',
                        (email, password_hash, first_name, last_name),
                    )
                    con.execute(
                        'INSERT OR IGNORE INTO zipcode (zip_code, city_id) '
                        'VALUES (?, ?) ',
                        (zip_code, city_id)
                    )
                    cur = con.execute(
                        'SELECT id '
                        'FROM account '
                        'WHERE email = ? ;',
                        (email,),
                    )
                    account_id = cur.fetchone()
                    con.execute(
                        'INSERT INTO seller (phone, zip_code, street, home, account_id ) '
                        'VALUES (?, ?, ?, ?, ?) ',
                        (phone, zip_code, street, home, account_id['id'])
                    )
                    cur = con.execute(
                        'SELECT account.id, '
                        '       email, '
                        '       first_name, '
                        '       last_name, '
                        '       phone, '
                        '       zipcode.zip_code, '
                        '       city_id, '
                        '       street, '
                        '       home, '
                        '       (seller.id IS NOT NULL) AS is_seller '
                        'FROM account '
                        'LEFT JOIN seller ON account.id = seller.account_id '
                        'JOIN zipcode ON seller.zip_code = zipcode.zip_code '
                        'WHERE email = ? ',
                        (email,),
                    )
                    user = cur.fetchone()

                except sqlite3.IntegrityError:
                    return 'Поле email должно быть уникальным', 409
            return jsonify(dict(user)), 201


class UserView(MethodView):
    @auth_required
    def get(self, user_id, user):
        with db.connection as con:
            cur = con.execute(
                'SELECT account.id, '
                '       email, '
                '       first_name, '
                '       last_name, '
                '       phone, '
                '       zipcode.zip_code, '
                '       city_id, '
                '       street, '
                '       home, '
                '       (seller.id IS NOT NULL) AS is_seller '
                'FROM account '
                'LEFT JOIN seller ON account.id = seller.account_id '
                'LEFT JOIN zipcode ON seller.zip_code = zipcode.zip_code '
                'WHERE account.id = ?  ',
                (user_id,),
            )
            user = dict(cur.fetchone())
        if user is None:
            return 'Такого пользователя нет', 404
        return jsonify({field: value for field, value in user.items() if value != None}), 200

    @auth_required
    def patch(self, user_id, user):
        if user_id != user['id']:
            return 'Вы можете редактировать только свой профиль', 403
        request_json = dict(request.json)
        account_data = {}
        seller_data = {}
        city_data = {}

        for key, values in request_json.items():
            if key in ('first_name', 'last_name',):
                account_data[key] = values
            if key in ('phone', 'zip_code', 'street', 'home',):
                seller_data[key] = values
            if key in ('zip_code', 'city_id',):
                city_data[key] = values

        account_params = ','.join(f'{key} = ?' for key in account_data)
        seller_params = ','.join(f'{key} = ?' for key in seller_data)

        if user['is_seller'] == request_json['is_seller']:
            query_account = f'UPDATE account SET {account_params} WHERE id = ?'
            query_seller = f'UPDATE seller SET {seller_params} WHERE account_id = ? '

            with db.connection as con:
                con.execute(query_seller, (*seller_data.values(), user_id))
                con.execute(query_account, (*account_data.values(), user_id))

                con.execute(
                    'INSERT OR IGNORE INTO zipcode (zip_code, city_id) '
                    'VALUES (?, ?) ',
                    (city_data['zip_code'], city_data['city_id'],),
                )

        else:
            with db.connection as con:
                cur = con.execute(
                    'SELECT seller.id AS seller_id, '
                    '       ad.id AS ad_id, '
                    '       adtag.id AS adtag_id, '
                    '       car.id AS car_id , '
                    '       carcolor.id AS carcolor_id '
                    'FROM account '
                    '     INNER JOIN seller ON account.id = seller.account_id '
                    '     INNER JOIN ad ON seller.id = ad.seller_id '
                    '     LEFT JOIN adtag ON ad.id = adtag.ad_id '
                    '     INNER JOIN car ON ad.car_id = car.id '
                    '     LEFT JOIN carcolor ON car.id = carcolor.car_id '
                    'WHERE account.id = ? ',
                    (user_id,),
                )

                list_id = dict(cur.fetchone())

            query_adtag = f'DELETE FROM adtag WHERE id = {list_id["adtag_id"]}'
            query_carcolor = f'DELETE FROM carcolor WHERE id = {list_id["carcolor_id"]}'
            query_car = f'DELETE FROM car WHERE id = {list_id["car_id"]}'
            query_ad = f'DELETE FROM ad WHERE id = {list_id["ad_id"]}'
            query_seller = f'DELETE FROM seller WHERE id = {list_id["seller_id"]}'

            with db.connection as con:
                con.execute(query_adtag)
                con.execute(query_carcolor)
                con.execute(query_car)
                con.execute(query_ad)
                con.execute(query_seller)

        return 'Вы обновили ваш профиль', 200


bp.add_url_rule('', view_func=UsersView.as_view('users'))
bp.add_url_rule('/<int:user_id>', view_func=UserView.as_view('user'))