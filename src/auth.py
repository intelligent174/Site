from functools import wraps

from flask import session

from database import db


def auth_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return 'Вам нужно авторизоваться', 403
        with db.connection as con:
            cur = con.execute(
                'SELECT account.id, '
                '       first_name, '
                '       last_name, '
                '       seller.id AS seller_id, '
                '       (seller.id IS NOT NULL) AS is_seller  '
                'FROM account '
                'LEFT JOIN seller ON account.id = seller.account_id '
                'WHERE account.id = ? ',
                (user_id,),
            )
            user = dict(cur.fetchone())
        if not user:
            return 'Пользователя по такому id нет', 403
        return view_func(*args, **kwargs, user=user)
    return wrapper
