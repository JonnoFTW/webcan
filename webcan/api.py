from pyramid.view import view_config
import json
import base64
import gzip

@view_config(route_name='api_upload', renderer="json")
def upload_vehicle(request):
    # take in some gzipped data that is base64 encoded
    key = request.POST.getall('apikey[]')
    # if key != request.db['webcan_devices'].find()
    data = request.POST.get('data')
    device_ids = set([])
    rows = []
    for row in base64.decode(data, 'ascii'):
        js = json.loads(row)
        device_ids.add(js['vid'])
        # check if we have all the appropriate keys for the devices we want to add

    request.db.insert()