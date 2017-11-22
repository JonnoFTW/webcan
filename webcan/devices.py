from pyramid.view import view_config
import pyramid.httpexceptions as exc
from pluck import pluck
import secrets
import re


@view_config(route_name='device_add', renderer='json')
def add_device(request):
    for f in ('dev_name', 'dev_make', 'dev_model', 'dev_type'):
        if re.findall(r"^[\w_]+$", request.POST[f]) is not None:
            return exc.HTTPBadRequest("Device fields must must only contain letters, numbers and underscores")
    try:
        doc = {
            'name': request.POST['dev_name'][:32],
            'secret': secrets.token_hex(32),
            'make': request.POST['dev_make'][:32],
            'model': request.POST['dev_model'][:32],
            'type': request.POST['dev_type'][:32]
        }
        request.db.webcan_devices.insert_one(doc)
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
