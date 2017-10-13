from pyramid.events import BeforeRender, subscriber, BeforeTraversal
from pyramid.security import remember, forget, Authenticated, Allow
from pyramid.renderers import render_to_response, get_renderer
from pyramid.view import view_config, notfound_view_config
from ldap3 import Server, Connection, ALL, NTLM
import pyramid.httpexceptions as exc
from datetime import datetime
from pluck import pluck
import secrets
import bcrypt
import os

import pymongo

LOGIN_TYPES = ['ldap', 'external']
USER_LEVELS = ['admin', 'viewer']


@view_config(route_name='home', renderer="templates/mytemplate.mako")
def home_view(request):
    return {'project': 'webcan'}


@view_config(route_name='devices', renderer='templates/device_list.mako')
def list_devices(request):
    return {}


def _get_user_devices(request):
    if request.authenticated_userid is None:
        return []
    user = request.db['webcan_users'].find_one({'username': request.authenticated_userid})
    query = {}
    if user['devices'] == '*':
        query = {}
    else:
        query = {'name': {'$in': user['devices']}}
    return list(request.db['webcan_devices'].find(query))


@subscriber(BeforeTraversal)
def check_logged_in(event):
    # if the user is not logged in and tries to access anything but /login,
    # redirect to /loging or send ajax error about not being logged in
    req = event.request
    if req.path in ('/login', '/logout', '/api/upload'):
        return
    if not req.user:
        if req.is_xhr:
            raise exc.HTTPBadRequest("You need to be logged in")
        else:
            raise exc.HTTPFound('/login')
    else:
        req.user['devices'] = sorted(_get_user_devices(req), key=lambda x: x['name'].lower(), reverse=True)


@subscriber(BeforeRender)
def add_device_global(event):
    if event['renderer_info'].type == '.mako':
        event['_pid'] = os.getpid()
        if event['request'].user is not None:
            event['devices'] = event['request'].user['devices']


@view_config(route_name='device', renderer='templates/device.mako')
def show_device(request):
    device_id = request.matchdict['device_id']

    return {
        'device': device_id,
        'trips': sorted(request.db['rpi_readings'].distinct('trip_id',
                                                            {'vid': device_id,
                                                             'pos': {'$ne': None}}
                                                            ),
                        reverse=True)
    }


@view_config(route_name='trip_json', renderer='bson')
def trip_json(request):
    trip_id = request.matchdict.get('trip_id', None)
    readings_query = {'trip_id': trip_id,'pos': {'$ne': None}}
    readings = list(
        request.db['rpi_readings'].find(readings_query, {'_id': False, 'vid': False, 'trip_id': False}).sort(
            [('trip_sequence', pymongo.ASCENDING)]))
    out = []
    for r in readings:
        if 'pos' not in r and 'latitude' in r:
            r['pos'] = {
                'type': 'Point',
                'coordinates': [r['longitude'], r['latitude']]
            }
            del r['latitude']
            del r['longitude']
        out.append(r)
    return {'readings': out}


def _prep_csv(query, header, rows):
    vid = None
    for row in query:
        if 'pos' in row:
            row['latitude'] = row['pos']['coordinates'][1]
            row['longitude'] = row['pos']['coordinates'][0]

        vid = row['vid']
        for f in ['vid', 'pos', 'trip_id']:
            if f in row:
                del row[f]

        header.update(row.keys())
        rows[row['trip_sequence']] = row
    # print("Headers are:", header)
    return vid


@view_config(route_name='fix_pos', renderer='bson')
def fix_pos(request):
    # request all those data with latitude and longitude set without pos
    query = {'pos': {'$exists': False}, 'latitude': {'$ne':0.0}}
    data = list(request.db.rpi_readings.find(query))
    # do this:
    """
    db.getCollection('rpi_readings').find({'pos': {'$exists': false}, 'latitude': {'$exists':true}}).snapshot().forEach(
    function(elem) {
        db.rpi_readings.update({_id:elem._id},
            {$set:{pos:{
                'type':'Point',
                'coordinates':[elem.longitude,elem.latitude]
                }},
                $unset:{latitude:"",longitude:""}
        })
    }
)
"""
    return {'data': data}
@view_config(route_name='trip_csv', renderer='csv')
def trip_csv(request):
    trip_id = request.matchdict.get('trip_id')

    # override attributes of response
    # iterate through the data, make a set of headers seen
    header = set()
    rows = {}
    query = request.db.rpi_readings.find({'trip_id': trip_id,'pos': {'$ne': None}}, {'_id': False}).sort(
        [('trip_sequence', pymongo.ASCENDING)])
    vid = _prep_csv(query, header, rows)
    filename = '{}_{}.csv'.format(vid.replace(' ', '_'), trip_id)
    request.response.content_disposition = 'attachment;filename=' + filename
    # put GPS fields first
    to_front = ['trip_sequence', 'timestamp', 'latitude', 'longitude', 'altitude', 'spd_over_grnd', 'num_sats']
    for i in to_front:
        header.remove(i)
    headers = to_front + sorted(header)
    return {
        'header': headers,
        'rows': sorted(rows.values(),key=lambda x:x['trip_sequence']),
    }


def get_device_trips_for_user(request):
    return list(
        request.db.rpi_readings.distinct('trip_id',
                                         {'vid': {'$in': pluck(request.user['devices'], 'name')},
                                          'timestamp': {'$ne': None}}))


@view_config(route_name='data_export', request_method='GET', renderer='templates/data_export.mako')
def data_export(request):
    # return those trips for vehicles belonging to this user

    trips = get_device_trips_for_user(request)
    return {
        'trips': trips
    }


@view_config(route_name='data_export', request_method='POST')
def data_export_out(request):
    post = request.POST
    query = {'pos': {'$exists': True, '$ne': None}}
    # print(post)
    if post['daterange']:
        from_dt, to_dt = map(lambda x: datetime.strptime(x, '%d/%m/%Y %I:%M %p'), post['daterange'].split(' - '))

        query['timestamp'] = {
            '$gte': from_dt,
            '$lte': to_dt
        }
    if 'selectDevices' in post and post['selectDevices']:
        query['vid'] = {'$in': post.getall('selectDevices')}
    if 'selectTrips' in post and post['selectTrips']:
        query['trip_id'] = {'$in': post.getall('selectTrips')}
    if post['map-hull']:
        points = list(map(float, post['map-hull'].split(',')))
        n = 2
        points = [points[i:i + n] for i in range(0, len(points), n)]
        points.append(points[0])
        query['pos'] = {'$geoWithin': {
            '$geometry': {
                'type': 'Polygon',
                'coordinates': [points]
            }
        }
        }
    # print(query)
    data = list(request.db.rpi_readings.find(query, {'_id': False}))
    if len(data) == 0:
        return render_to_response(
            'templates/data_export.mako',
            {'detail': 'No data returned from query',
             'trips': get_device_trips_for_user(request)},
            request
        )
    renderers = ['shp', 'bson', 'csv']
    if post['selectFormat'] in renderers:
        renderer = post['selectFormat']
    else:
        renderer = 'bson'

    if renderer == 'csv':
        headers = set()
        rows = []
        _prep_csv(data, headers, rows)
        data = {
            'header': list(headers),
            'rows': rows,
        }
    renderer_obj = get_renderer(renderer)
    request.response.content_type = renderer_obj.content_type
    request.response.content_disposition = 'attachment;filename=webcan_export_{}.{}'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S'), renderer_obj.content_type.split('/')[1])
    return render_to_response(
        renderer_name=renderer,
        value=data,
        request=request,
        response=request.response
    )


@notfound_view_config(renderer='templates/404.mako')
def notfound(request):
    request.response.status = 404
    return {}


@view_config(route_name='login', renderer='templates/login.mako')
def login(request):
    login_url = request.resource_url(request.context, 'login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    # if post data is set, try to login,
    message_def = 'Please provide a valid username and password'
    username = ''
    password = ''

    if 'form.submitted' in request.params:
        message = message_def
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if not (username is None or password is None):
            user = request.db['webcan_users'].find_one({'username': username})
            if user is not None:
                if user.get('login', None) == 'ldap':
                    is_valid = check_credentials(username, password)
                else:  # if user['login'] == 'external':
                    is_valid = check_pass(password, user['password'])
                if is_valid:
                    # actually log the user in and take them to the front page!
                    headers = remember(request, user['username'])
                    return exc.HTTPFound(location=came_from, headers=headers)

    else:
        message = ''

    return dict(
        message=message,
        url=request.application_url + '/login',
        came_from=came_from,
        username=username,
        password=password,
    )


@view_config(route_name='device_add', renderer='json')
def add_device(request):
    try:
        doc = {
            'name': request.POST['dev_name'],
            'secret': secrets.token_hex(32),
            'make': request.POST['dev_make'],
            'model': request.POST['dev_model'],
            'type': request.POST['dev_type']
        }
        dev = request.db.webcan_devices.insert_one(doc)

    except Exception as e:
        return exc.HTTPBadRequest('Please provide all fields and a unique name')
    del doc['_id']
    return doc


@view_config(route_name='trips_of_device', renderer='bson')
def trips_of_device(request):
    req_devices = set(request.GET.getall('devices[]'))
    user_devices = set(pluck(request.user['devices'], 'name'))
    if len(req_devices) == 0:
        devices = user_devices
    else:
        devices = req_devices & user_devices
    trips = list(request.db.rpi_readings.distinct('trip_id', {'vid': {'$in': list(devices)}}))
    trips_with_vid = [request.db.rpi_readings.find_one({'trip_id': x, 'vid': {'$exists': True}},
                                                       {'_id': False, 'trip_id': True, 'vid': True}) for x in trips]
    return {
        'trips': trips_with_vid
    }


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return exc.HTTPFound(location='/login', headers=headers)


@view_config(route_name='user_list', renderer='templates/users.mako')
def user_list(request):
    return {
        'users': request.db.webcan_users.find({}),
        'user_levels': USER_LEVELS,
        'login_types': LOGIN_TYPES
    }


@view_config(route_name='user_add', renderer='bson')
def user_add(request):
    new_fan = request.POST.get('fan', None)
    if new_fan is None or request.db.webcan_users.find_one({'username': new_fan}) is not None:
        return {
            'err': 'Empty or existing usernames cannot be used again'
        }
    new_user_obj = {
        'username': new_fan,
        'login': 'ldap',
        'devices': [],
        'secret': secrets.token_hex(32),
        'level': 'viewer'
    }

    request.db.webcan_users.insert_one(new_user_obj)
    return new_user_obj


def check_pass(password, hashed):
    return bcrypt.checkpw(password, hashed)
    # return hashlib.sha512(password.encode()).hexdigest()


def check_credentials(username, password):
    """Verifies credentials for username and password.
    Returns True on success or False on failure
    """
    ldap_user = '\\{}@flinders.edu.au'.format(username)
    server = Server('ad.flinders.edu.au', use_ssl=True)

    connection = Connection(server, user=ldap_user, password=password, authentication=NTLM)
    try:
        return connection.bind()
    except:
        return False
