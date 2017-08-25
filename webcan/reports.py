import numpy as np
from pyramid.view import view_config
from .views import get_device_trips_for_user
import pymongo

@view_config(route_name='report_list', renderer="templates/reports/list_reports.mako")
def report_list(request):
    introspector = request.registry.introspector
    reports = [
        i for i in introspector._categories['routes'].values() if
        i['pattern'].startswith('/report/') and '{' not in i['pattern']
    ]
    return {'reports': reports}


@view_config(route_name='report_phase', request_method='GET', renderer="templates/reports/phase_classify.mako")
def phase_classify(request):
    return {'trips': get_device_trips_for_user(request), 'docs': _classify_readings_with_phases.__doc__}


@view_config(route_name='report_phase', request_method='POST', renderer="bson")
def phase_classify_render(request):
    readings = list(request.db.rpi_readings.find({
        'trip_id': {'$in':request.POST.getall('trips[]')},
        'PID_SPEED (km/h)': {'$ne': None},
        'timestamp': {'$exists': True}
    },
        {'_id': False}).sort([('timestamp', pymongo.ASCENDING)]))
    _classify_readings_with_phases(readings)
    return {'readings': readings[75:150]}


def _classify_readings_with_phases(readings):
    """
    Classify readings with the following schema:
       -1. N/A
        0. Idle at 0
        1. Acceleration from 0
        2. Cruise
        3. Deceleration to 0
        4. Intermediate acceleration
        5. Intermediate deceleration
    """
    speed = 'PID_SPEED (km/h)'
    phase = 'phase'
    # load into numpy
    last = None
    from_zero = True
    cruise_thresh = 4
    phase_count = 0
    for r in readings:
        if r[speed] <= 5:
            r[phase] = 0
        elif last is not None and phase in last:
            if last[phase] == 0 and r[speed] != 0:
                last[phase] = 1
                r[phase] = 1
            if last[phase] == 1:
                if r[speed] < last[speed]:
                    r[phase] = 2
                else:
                    r[phase] = 1
            if last[phase] == 2:
                diff = last[speed] - r[speed]
                if diff >= 5:
                    r[phase] = 5
                elif diff <= -5:
                    r[phase] = 4
                else:
                    r[phase] = 2
        if phase not in r:
            r[phase] = 6
        last = r
