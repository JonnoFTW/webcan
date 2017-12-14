from pyramid.view import view_config, notfound_view_config, forbidden_view_config, exception_view_config
from pyramid.renderers import render_to_response, get_renderer
from pyramid.events import BeforeRender, subscriber
import pyramid.httpexceptions as exc
from datetime import datetime
from .utils import calc_extra
from pluck import pluck
import platform
import pymongo
import pymongo.errors
import os

LOGIN_TYPES = ['ldap', 'external']
USER_LEVELS = ['admin', 'viewer']


@view_config(route_name='home', renderer="templates/home.mako")
def home_view(request):
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
    return list(request.db['webcan_devices'].find(query, {'_id': 0}).sort([('name', pymongo.ASCENDING)]))


@subscriber(BeforeRender)
def add_device_global(event):
    if event['renderer_info'].type == '.mako':
        event['_pid'] = os.getpid()
        event['_host'] = platform.node()
        if event['request'].user is not None:
            event['devices'] = event['request'].user['devices']


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
    query = {'pos': {'$exists': False}, 'latitude': {'$ne': 0.0}}
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
    query = request.db.rpi_readings.find({'trip_id': trip_id, 'pos': {'$ne': None}}, {'_id': False}).sort(
        [('trip_sequence', pymongo.ASCENDING)])
    vid = _prep_csv(query, header, rows)
    filename = '{}_{}.csv'.format(vid.replace(' ', '_'), trip_id)
    request.response.content_disposition = 'attachment;filename=' + filename
    # put GPS fields first
    to_front = ['trip_sequence', 'timestamp', 'latitude', 'longitude', 'altitude', 'spd_over_grnd', 'num_sats']
    for i in to_front:
        if i in header:
            header.remove(i)
    headers = to_front + sorted(header)
    return {
        'header': headers,
        'rows': sorted(rows.values(), key=lambda x: x['trip_sequence']),
    }


def get_device_trips_for_user(request):
    return list(
        request.db.rpi_readings.distinct('trip_id',
                                         {'vid': {'$in': pluck(request.user['devices'], 'name')}}))


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


@forbidden_view_config(renderer='templates/exceptions/403.mako')
def forbidden(request):
    request.response.status = 403
    return {}


@notfound_view_config(renderer='templates/exceptions/404.mako')
def notfound(request):
    request.response.status = 404
    return {}


@exception_view_config(pymongo.errors.NetworkTimeout, renderer='templates/exceptions/503.mako')
def service_unavailable(request):
    return {'msg'}


@view_config(context=exc.HTTPBadRequest)
def bad_request(exception, request):
    if request.is_xhr:
        exception.content_type = 'application/json'
    return exception


class AJAXHttpBadRequest(exc.HTTPBadRequest):
    def doJson(self, status, body, title, environ):
        return {'message': self.detail,
                'code': status,
                'title': self.title}

    def __init__(self, detail):
        exc.HTTPBadRequest.__init__(self, detail, json_formatter=self.doJson)

        self.content_type = 'application/json'
