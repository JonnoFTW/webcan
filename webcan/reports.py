from .views import get_device_trips_for_user
from pyramid.view import view_config
from geopy.distance import vincenty
from collections import deque
from pluck import pluck
import numpy as np
import pymongo

speed = 'PID_SPEED (km/h)'
phase = 'phase'
trip_sequence = 'trip_sequence'


@view_config(route_name='report_list', renderer="templates/reports/list_reports.mako")
def report_list(request):
    introspector = request.registry.introspector
    reports = set([
        i for i in introspector._categories['routes'].values() if
        i['pattern'].startswith('/report/') and '{' not in i['pattern']
    ])
    return {'reports': reports}


@view_config(route_name='report_phase', request_method='GET', renderer="templates/reports/phase_classify.mako")
def phase_classify(request):
    return {
        'trips': get_device_trips_for_user(request),
        'docs': _classify_readings_with_phases.__doc__
    }


@view_config(route_name='report_phase', request_method='POST', renderer="bson")
def phase_classify_render(request):
    readings = list(request.db.rpi_readings.find({
        'trip_id': {'$in': request.POST.getall('trips[]')},
        'PID_SPEED (km/h)': {'$ne': None},
        'timestamp': {'$exists': True, '$ne': None},
        'pos': {'$ne': None}
    },
        {'_id': False}).sort([('timestamp', pymongo.ASCENDING)]))
    _classify_readings_with_phases_pas(readings)
    summary = _summarise_readings(readings)
    return {
        'readings': readings,
        'summary': summary
    }


def _summarise_readings(readings):
    """
    Break down readings into
    :param readings:
    :param phases:
    :return:
    """
    return {
        'Distance': round(sum(map(lambda x: vincenty(x[0]['coordinates'], x[1]['coordinates']).kilometers,
                                  zip(pluck(readings, 'pos'), pluck(readings[1:], 'pos')))), 4),
    }


def _classify_readings_with_phases_pas(readings):
    def idle_pass():
        # do Idle pass

        for i in readings:
            if i[speed] == 0:
                i[phase] = 1
            else:
                i[phase] = 6

    def accel_from_stop():
        # do accel from stop
        acc_start = None
        acc_finish = None
        found_start_idle = False
        for idx, i in enumerate(readings):
            if idx + 6 > len(readings):
                break
            i1, i2, i3, i4, i5 = readings[idx + 1:idx + 6]
            if i[phase] == 1:
                found_start_idle = True
            if found_start_idle and i[phase] != 1:
                if acc_start is None:
                    acc_start = idx
                if all([i[speed] >= i1[speed],
                        i[speed] > i1[speed],
                        i[speed] > i2[speed] - 0.5,
                        i[speed] > i3[speed] - 1,
                        i[speed] > i4[speed] - 1.5,
                        i[speed] > i5[speed] - 2.0]):
                    acc_finish = idx
                    #     for trips between acc_start and acc_finish, mark phase = 2:
                    for t in readings[acc_start:acc_finish]:
                        t[phase] = 2
                    acc_finish = None
                    acc_start = None

    def decel_to_stop():
        dec_start = 1
        dec_finish = 1
        found_end_idle = False
        dec_finish_time_set = False
        for idx, i in enumerate(reversed(readings)):
            idx = len(readings) - idx
            if i[phase] == 1:
                found_end_idle = True
            if found_end_idle and i[phase] != 1:
                if dec_finish_time_set == False:
                    dec_finish = idx
                    dec_finish_time_set = True
                if all([i[speed] >= readings[idx - 1][speed],
                        i[speed] > readings[idx - 2][speed] - 0.5,
                        i[speed] > readings[idx - 3][speed] - 1,
                        i[speed] > readings[idx - 4][speed] - 1.5,
                        i[speed] > readings[idx - 5][speed] - 2.0]):
                    dec_start = idx
                    for j in range(dec_start, dec_finish + 1):
                        readings[j][phase] = 3
                    found_end_idle = False
                    dec_finish_time_set = False

    def accel_decel():

        # classify intermediate accel decel
        tStart = 1
        tk = 1
        tEnd = 1
        tMin = 1
        tMax = 1
        for idx, i in enumerate(readings):
            if i == tStart:
                j = 0
                if 1.05 * readings[tStart][speed] + 5.0 > 15:
                    vxa = 1.05 * readings[tStart][speed] + 5.0 > 15
                else:
                    vxa = 15
                vxd = (readings[tStart] - 5) / 1.05
                j = tStart
                if readings[tStart][speed] > 15:
                    while not (readings[j][speed] > vxa) or readings[j][speed] <= vxd:
                        j += 1
                else:
                    while not (readings[j][speed] >= vxa):
                        j += 1
                tk = j
                j = 0
                if readings[tStart][speed] < readings[tk][speed]:
                    for j in range(tk, tStart, -1):
                        if all([readings[j][speed] <= readings[j - 1][speed],
                                readings[j][speed] < readings[j - 2][speed] + 0.5,
                                readings[j][speed] < readings[j - 3][speed] + 1.0,
                                readings[j][speed] < readings[j - 4][speed] + 1.5,
                                readings[j][speed] < readings[j - 5][speed] + 2.0]):
                            tStart = j
                            break


    def cruise():
        duration_limit = 4

        for i in readings:
            if i[phase] == 6:
                pass

    idle_pass()
    accel_from_stop()
    decel_to_stop()
    accel_decel()
    cruise()


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

    # load into numpy
    phase_len = 3
    for r in readings[:phase_len]:
        r[phase] = 0
    last_series = deque(readings[:phase_len], maxlen=5)
    last = None
    from_zero = True
    cruise_thresh = 4
    phase_count = 0
    phase_min_time = 5
    last_cruise_phase = 0
    idx = phase_len
    dec_angle = 14
    for r in readings[phase_len:]:
        last_series.append(r)
        r[phase] = 0
        idx += 1
        # add elements to the deque,
        # check the angle between the first and last points
        angle = np.arctan2(last_series[-1][speed] - last_series[0][speed],
                           last_series[-1]['timestamp'].timestamp() - last_series[0]['timestamp'].timestamp())
        angle = np.degrees(angle)

        if r[speed] <= 5:
            r[phase] = 0
            last_cruise_phase = 0
            # if last_cruise_phase == 2:
            #     # we need to roll back and mark those previous ones as dec2zero (3)
            #     rb = 1
            #     while 1:
            #         lr = readings[idx-rb]
            #         rb += 1
            #         if lr[phase] == 2:
            #             lr[phase] = 3
            #             break
            #         else:
            #             lr[phase] = 3
            # else:
        elif -10 < angle < 10:
            r[phase] = 2
            last_cruise_phase = 2
        elif angle < -dec_angle:
            r[phase] = 5
        elif angle > dec_angle:
            if last_cruise_phase == 2:
                r[phase] = 4
            else:
                r[phase] = 1
        else:
            r[phase] = 0
        r['angle'] = angle
        print("{}\t{}\t{}\t{}".format(r['trip_sequence'], angle, r[speed], r[phase]))
        """
           Make sure all the readings in last_series are
           within phase_min_time of the last_reading
        """
        # last_series = [i for i in last_series if (i[-1]['timestamp'] - i['timestamp']).total_seconds() <phase_min_time]
    return
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
        last_series.append(r)
