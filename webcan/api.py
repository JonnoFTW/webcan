from pyramid.view import view_config
from pyramid.httpexceptions import HTTPForbidden, HTTPBadRequest
import json
import base64
import gzip


@view_config(route_name='api_upload', renderer="json")
def upload_vehicle(request):
    # take in some gzipped data that is base64 encoded
    keys = request.POST.get('keys')
    if keys is None:
        return HTTPBadRequest("Please specify the device keys")
    keys = keys.split(",")
    # if key != request.db['webcan_devices'].find()
    # we receive the data as base 64 encoded gzipped json object rows
    data = request.POST.get('data')
    if data is None:
        return HTTPBadRequest("Please provide a data value")
    data64 = bytes(data, 'ascii')

    device_ids = set([])
    trips = set()
    rows = []
    for row in gzip.decompress(base64.b64decode(data64)).decode('ascii').splitlines():
        js = json.loads(row)
        if 'vid' not in js or 'trip_id' not in js:
            return HTTPBadRequest("Please provide a vid and trip_id on every row")
        device_ids.add(js['vid'])
        trips.add(js['trip_id'])
        rows.append(js)
    # check if we have all the appropriate keys for the devices we want to add
    for device in request.db.webcan_devices.find({'name': {'$in': device_ids}}):
        if device['secret'] not in keys:
            return HTTPForbidden('You must provide a valid API key for all Vehicle IDs used')

    return
    request.db.rpi_readings.delete({'trip_id': {'$in': trips}})
    return request.db.insert_many(rows)

