import pymongo
from datetime import datetime

from pyramid.renderers import render_to_response, get_renderer
from pyramid.view import view_config

from webcan.views import get_device_trips_for_user


@view_config(route_name='data_export', request_method='GET', renderer='templates/data_export.mako')
def data_export(request):
    # return those trips for vehicles belonging to this user

    trips = get_device_trips_for_user(request)
    return {
        'trips': trips
    }


@view_config(route_name='trip_csv', renderer='csv')
def trip_csv(request):
    trip_id = request.matchdict.get('trip_id')

    # override attributes of response
    # iterate through the data, make a set of headers seen
    header = set()
    rows = []
    query = request.db.rpi_readings.find({'trip_id': trip_id, 'pos': {'$ne': None}}, {'_id': False}).sort(
        [('trip_sequence', pymongo.ASCENDING)])
    vid, header = _prep_csv(query, header, rows)
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
        'rows': rows,
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
    print(query)
    data = list(request.db.rpi_readings.find(query, {'_id': False}).sort([('trip_id', pymongo.ASCENDING),
                                                                          ('trip_sequence', pymongo.ASCENDING)]))
    if len(data) == 0:
        return render_to_response(
            'templates/data_export.mako',
            {'detail': 'No data returned from query',
             'trips': get_device_trips_for_user(request)},
            request
        )
    renderers = ['shp', 'bson', 'csv', 'sqlite']
    if post['selectFormat'] in renderers:
        renderer = post['selectFormat']
    else:
        renderer = 'bson'

    if renderer == 'csv':
        headers = set()
        rows = []
        _, headers = _prep_csv(data, headers, rows)
        data = {
            'header': headers,
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


def _prep_csv(query, header, rows):
    vid = None
    prev = None
    for idx, row in enumerate(query):
        if 'pos' in row:
            row['latitude'] = row['pos']['coordinates'][1]
            row['longitude'] = row['pos']['coordinates'][0]

        vid = row['vid']
        for f in ['vid', 'pos']:
            if f in row:
                del row[f]
        if prev is not None and prev['trip_id'] != row['trip_id']:
            prev = None
        if prev is not None:
            row['dist(m)'] = (row['timestamp'] - prev['timestamp']).total_seconds() * row['spd_over_grnd'] * 0.277778
        else:
            row['dist(m)'] = 0
        header.update(row.keys())
        # rows[row['trip_sequence']] = row
        rows.append(row)
        prev = row
    to_front = ['trip_sequence', 'timestamp', 'latitude', 'longitude', 'altitude', 'spd_over_grnd', 'num_sats',
                'dist(m)']
    for i in to_front:
        if i in header:
            header.remove(i)
    headers = to_front + sorted(header)
    # print("Headers are:", header)
    return vid, headers
