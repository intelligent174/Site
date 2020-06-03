from exceptions import ServiceError


class AdsServiceError(ServiceError):
    service = 'ads'


class AdDoesNotExistError(AdsServiceError):
    pass


class AdsService:
    def __init__(self, connection):
        self.connection = connection

    def get_ads(self, user_id=None):
        query = (
            'SELECT * '
            'FROM ad '
            'JOIN seller ON ad.seller_id = seller.id '
            'LEFT JOIN account ON seller.account_id = account.id '
        )
        params = ()
        if user_id is not None:
            query += 'WHERE account.id  = ?'
            params = (user_id,)
        cur = self.connection.execute(query, params)
        ads = cur.fetchall()
        return [dict(ad) for ad in ads]

    def get_ad(self, ad_id):
        query = (
            'SELECT ad.id, '  
            '       seller_id, '  
            '       ad.title, '  
            '       ad.date, '  
            '       tag.name, '  
            '       make, '  
            '       model, '  
            '       color.id, '  
            '       color.name, '  
            '       color.hex  '  
            '       mileage, '  
            '       num_owners, '  
            '       reg_number, '  
            '       image.title, '  
            '       image.url, '  #
            '       carcolor.color_id '       
            'FROM ad '
            'LEFT JOIN seller ON ad.seller_id = ad.id '
            'JOIN adtag ON ad.id = adtag.ad_id '
            'JOIN tag ON adtag.tag_id = tag.id  '
            'JOIN car ON ad.car_id = car.id '
            'JOIN image ON car.id = image.car_id '
            'JOIN carcolor ON car.id = carcolor.car_id '
            'JOIN color ON carcolor.color_id = color.id '
            'WHERE ad.id = ?'
        )
        params = (ad_id,)
        cur = self.connection.execute(query, params)
        ad = cur.fetchone()
        if ad is None:
            raise AdDoesNotExistError(ad_id)
        return dict(ad), 200

