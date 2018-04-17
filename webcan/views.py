from pyramid.view import view_config
from pyramid.events import BeforeRender, subscriber
from pluck import pluck
import platform
import pymongo
import pymongo.errors
import os
import subprocess

LOGIN_TYPES = ['ldap', 'external']
USER_LEVELS = ['admin', 'viewer']


@view_config(route_name='home', renderer="templates/home.mako")
def home_view(request):
    return {}


def _get_user_devices_ids(request):
    objs = _get_user_devices(request)
    return pluck(objs, 'name')
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
    if event['request'].exception:
        return
    if event['renderer_info'].type == '.mako':
        event['_pid'] = os.getpid()
        event['_host'] = platform.node()
        if event['request'].user is not None:
            event['devices'] = event['request'].user['devices']


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


def get_device_trips_for_user(request):
    return list(
        request.db.rpi_readings.distinct('trip_id',
                                         {'vid': {'$in': pluck(request.user['devices'], 'name')}}))


@view_config(route_name='changelog', request_method='GET', renderer='templates/changelog.mako')
def changelog(request):
    # show the changelog

    changes = subprocess.check_output(["git", "log",
                                       "--pretty=tformat:<a href='https://github.com/JonnoFTW/webcan/commit/%h'>%h</a> %an, %ar:<p>%B</p>"]).decode(
        'utf-8').replace('\n', '<br>').replace('</p><br>', '</p>')
    return {
        'changes': changes
    }
