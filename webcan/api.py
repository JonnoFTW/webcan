from pyramid.view import view_config
from pyramid.httpexceptions import HTTPForbidden, HTTPBadRequest
import json
import base64
import gzip
import dateutil.parser
from pytz import timezone, utc


@view_config(route_name='api_upload', renderer="json")
def upload_vehicle(request):
    # take in some gzipped data that is base64 encoded
    keys = request.POST.get('keys')
    tz_local = timezone('Australia/Adelaide')
    tz_utc = utc
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
    # create a new trip_id based off the first GPS time reading
    timestamps = {}
    new_trip = True
    for row in gzip.decompress(base64.b64decode(data64)).decode('ascii').splitlines():
        try:
            js = json.loads(row)
        except json.JSONDecodeError as e:
            # print("Could not decode '{}': {}".format(row, e))
            continue
        if 'vid' not in js or 'trip_id' not in js:
            return HTTPBadRequest("Please provide a vid and trip_id on every row")

        if 'timestamp' in js and js['timestamp'] is not None:
            js['timestamp'] = dateutil.parser.parse(js['timestamp'])

            if js['trip_id'] not in timestamps:
                try:
                    timestamps[js['trip_id']] = js['timestamp'].astimezone(tz_local).strftime("%Y%m%d_%H%M%S_{}".format('_'.join(js['trip_id'].split('_')[2:])))
                    # print("Changing {} to {}".format(js['trip_id'], timestamps[js['trip_id']]))
                    if new_trip:
                        if request.db.rpi_readings.find_one({'trip_id': timestamps[js['trip_id']]}) is not None:
                            print("Skipping:", js['trip_id'])
                            return {'msg': "Already seen this trip, skipping"}
                        else:
                            # we can go ahead with adding this trip
                            print("Adding", js['trip_id'])
                            new_trip = False
                except:
                    pass
        else:
            continue
        device_ids.add(js['vid'])
        trips.add(js['trip_id'])
        rows.append(js)
    # check if we have all the appropriate keys for the devices we want to add
    for device in request.db.webcan_devices.find({'name': {'$in': list(device_ids)}}):
        if device['secret'] not in keys:
            return HTTPForbidden('You must provide a valid API key for all Vehicle IDs used')
    for row in rows:
        row['trip_id'] = timestamps[row['trip_id']]
    if len(rows) < 30:
        return {
            'msg': 'Trip is too short to be of use and was rejected'
        }
    request.db.rpi_readings.remove({'trip_id': {'$in': list(trips)+list(timestamps.values())}})
    if not rows:
        return {'inserted': 0}
    res = request.db.rpi_readings.insert_many(rows)
    return {
        'inserted': len(res.inserted_ids)
    }

