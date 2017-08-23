from pymongo import MongoClient
from pyramid.config import Configurator
from pyramid.security import unauthenticated_userid
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

try:
    # for python 2
    from urlparse import urlparse
except ImportError:
    # for python 3
    from urllib.parse import urlparse

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_mako')
    if 'mongo_uri' in settings:
        db_url = urlparse(settings['mongo_uri'])
    else:
        import os
        db_url = urlparse(os.getenv("WEBCAN_MONGO_URI"))

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.add_route('devices', '/dev')
    config.add_route('device', '/dev/{device_id}')
    config.add_route('device_add', '/dev_add')

    config.add_route('map', '/map')

    config.add_route('user_list', '/users')
    config.add_route('user_manage', '/users/{user_id}')

    config.add_route('trip_csv', '/trip/{trip_id}.csv')
    config.add_route('trip_json', '/trip/{trip_id}.json')
    config.add_route('data_export', '/export')
    config.add_route('trips_of_device', '/dev_trips')

    config.add_route('report_list', '/report')
    config.add_route('report_phase', '/report/phase/')
    config.add_route('report_phase_classify', '/report/phase/{trip_id}')

    def add_db(request):
        conn = MongoClient(db_url.geturl())
        db = conn[db_url.path[1:]]

        def conn_close(request):
            conn.close()
        request.add_finished_callback(conn_close)
        return db

    def get_user(request):
        userid = unauthenticated_userid(request)
        if userid is not None:
            return request.db['webcan_users'].find_one({'username': request.authenticated_userid})

    def auth_callback(uid, request):

        user = request.db['webcan_users'].find_one({'username': uid})
        if user is not None:
            return ['auth']

    auth_policy = AuthTktAuthenticationPolicy('r4k4j5k4j56t5^%TGGfgrtRDFr', callback=auth_callback, hashalg='sha512')
    config.set_authentication_policy(auth_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(add_db, 'db', reify=True)

    config.add_renderer('bson', 'webcan.renderers.BSONRenderer')
    config.add_renderer('pymongo_cursor', 'webcan.renderers.PyMongoCursorRenderer')
    config.add_renderer('csv', 'webcan.renderers.CSVRenderer')
    config.add_renderer('shp', 'webcan.renderers.ShapefileRenderer')

    config.scan()
    return config.make_wsgi_app()
