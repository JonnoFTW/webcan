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

    import os
    if 'mongo_uri' in settings:
        db_url = urlparse(settings['mongo_uri'])
    else:
        db_url = urlparse(os.getenv("WEBCAN_MONGO_URI"))
        settings['ldap_server'] = os.getenv('LDAP_SERVER')
        settings['ldap_suffix'] = os.getenv('LDAP_USERNAME_SUFFIX')
        settings['auth_ticket_key'] = os.getenv('AUTH_TICKET_KEY')
        settings['smtp_domain'] = os.getenv('SMTP_DOMAIN')
        settings['smtp_from'] = os.getenv('SMTP_FROM')

    config = Configurator(settings=settings)
    config.include('pyramid_mako')
    config.add_static_view('static', 'webcan:static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.add_route('devices', '/dev')
    config.add_route('device', '/dev/{device_id}')
    config.add_route('device_add', '/dev_add')

    config.add_route('map', '/map')

    config.add_route('user_list', '/users')
    config.add_route('user_manage', '/users/v/{user_id}')
    config.add_route('user_add', '/users/add')
    config.add_route('reset_user_password', '/users/reset/{user_id}')

    config.add_route('trip_csv', '/trip/{trip_id}.csv')
    config.add_route('trip_json', '/trip/{trip_id}.json')
    config.add_route('data_export', '/export')
    config.add_route('trips_of_device', '/dev_trips')

    config.add_route('report_list', '/report')
    config.add_route('report_phase', '/report/phase')

    config.add_route('api_upload', '/api/upload')
    config.add_route('fix_pos', '/fix_pos')
    config.add_route('external_reset', '/reset_password')

    def add_db(request):
        conn = MongoClient(db_url.geturl(),
                           serverSelectionTimeoutMS=2500,
                           connectTimeoutMS=5000,
                           socketTimeoutMS=5000,
                           maxPoolSize=100,
                           maxIdleTimeMs=30000,
                           appname='webcan')
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

    auth_policy = AuthTktAuthenticationPolicy(settings['auth_ticket_key'], callback=auth_callback, hashalg='sha512')
    config.set_authentication_policy(auth_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(add_db, 'db', reify=True)

    config.add_renderer('bson', 'webcan.renderers.BSONRenderer')
    config.add_renderer('pymongo_cursor', 'webcan.renderers.PyMongoCursorRenderer')
    config.add_renderer('csv', 'webcan.renderers.CSVRenderer')
    config.add_renderer('shp', 'webcan.renderers.ShapefileRenderer')

    config.scan()
    app = config.make_wsgi_app()
    return app