from datetime import timedelta
from .utils import calc_extra
from .views import get_device_trips_for_user
from pyramid.view import view_config
from geopy.distance import vincenty
from collections import deque, defaultdict
from pluck import pluck
import numpy as np
import pymongo

from itertools import groupby

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
    query = {
        'timestamp': {'$exists': True, '$ne': None},
        'pos': {'$ne': None}
    }
    # print(request.POST)
    min_phase_time = int(request.POST.get('min-phase-seconds'))
    if request.POST.getall('trips[]'):
        query['trip_id'] = {'$in': request.POST.getall('trips[]')}
    if request.POST.getall('devices[]'):
        query['vid'] = {'$in': request.POST.getall('devices[]')}
    cursor = request.db.rpi_readings.find(query,
                                          {'_id': False}).sort([('timestamp', pymongo.ASCENDING)])

    print("Len readings:", cursor.count())
    readings = list(cursor)
    speed = _classify_readings_with_phases_pas(readings, min_phase_time)
    summary = _summarise_readings(readings)
    return {
        'readings': readings,
        # 'readings': [],
        'summary': summary,
        'speed_field': speed
    }


def per_phase_report(readings):
    phases = []
    for idx, phase_group in enumerate(
            [(key, list(group)) for key, group in (groupby(readings, key=lambda x: x[phase]))]):
        phase_type = phase_group[0]
        phase_no = idx
        p = phase_group[1]
        speeds = pluck(p, 'speed')
        phases.append({
            'date': p[0]['timestamp'].date(),
            'phasetype': phase_type,
            'phase_no': phase_no,
            'Start Time': p[0]['timestamp'].time(),
            'Finish Time': p[-1]['timestamp'].time(),
            'Duration': (p[-1]['timestamp'] - p[0]['timestamp']).total_seconds(),
            'Avg Temp': np.mean(pluck(p, '')),
            'Distance': 0,
            'Start Speed': speeds[0],
            'Finish Speed': speeds[-1],
            'Min Speed': np.min(speeds),
            'Max Speed': np.max(speeds),
            'Mean Speed': np.mean(speeds),
            'STdev Speed': np.std(speeds),
            'Coeff Beta': 0,
            'Y Intercept': 0,
            'Min Acc': 0,
            'Max Acc': 0,
            'Mean Acc': 0,
            'STDEV Acc': 0,
            'Total Fuel': 0,
            'Min Fuel rate': 0,
            'Max Fuel Rate': 0,
            'Mean Fuel Rate': 0,
            'STDEV Fuel Rate': 0,
            'Mean NOX': 0,
            'STDEV NOx': 0,
            'Mean HC': 0,
            'STDEV HC': 0,
            'Mean CH4': 0,
            'STDEV CH4': 0,
            'Mean CO': 0,
            'STDEV CO': 0,
            'Mean CO2': 0,
            'STDEV CO2': 0,
            'Mean FC': 0,
            'STDEV FC': 0,
            'Mean PM': 0,
            'STDEV PM': 0,
            'Mean OP': 0,
            'STDEV OP': 0

        })
    return phases


def _summarise_readings(readings):
    """
    Break down readings into individual trips and provide stats

    Then aggregate and provide stats for each vehicle
    :param readings:
    :param phases:
    :return:
    """
    trips = defaultdict(list)
    vehicles = defaultdict(list)
    vid_trips = {}
    for r in readings:
        trips[r['trip_id']].append(r)
        vehicles[r['vid']].append(r)
        vid_trips[r['trip_id']] = r['vid']

    def make_stats(_readings):

        out = {}
        for key, val in _readings.items():
            if not val:
                continue
            dist = 0
            duration = 0
            phases = {"Phase {}".format(i): 0 for i in range(7)}
            # print(val)
            start = val[0]['timestamp']
            for r1, r2 in zip(val, val[1:]):
                if r1['trip_id'] != r2['trip_id']:
                    duration += (r1['timestamp'] - start).total_seconds()
                    start = r2['timestamp']
                    continue
                dist += vincenty(r1['pos']['coordinates'], r2['pos']['coordinates']).kilometers

                phases["Phase {}".format(r1[phase])] += 1
            duration += (val[-1]['timestamp'] - start).total_seconds()
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            usages = [
                'Total CO2 (g)',
                'Petrol Used (ml)',
                'Petrol CO2 (g)',
                'Petrol cost (c)',
                'E Used (kWh)',
                'E CO2 (g)',
                'E cost (c)',
                'Total CO2 (g)'
            ]
            out[key] = {
                'Duration': "%d:%02d:%02d" % (h, m, s),
                'Distance (km)': round(dist, 4),
            }
            for field in usages:
                out[key][field] = round(sum(pluck(val, field, default=0)), 2)
            out[key].update({k: "{} ({:.2f}%)".format(v, 100 * v / len(val)) for k, v in phases.items()})
        return out

    trip_stats = make_stats(trips)
    vehicle_stats = make_stats(vehicles)
    aggregate_stats = make_stats({'Aggregate': readings})
    return {
        'Trips': trip_stats,
        'Vehicles': vehicle_stats,
        'Aggregate': aggregate_stats,
        '_vid_trips': vid_trips
    }


def _classify_readings_with_phases_pas(readings, min_phase_time):
    IDLE = 0
    ACCEL_FROM_ZERO = 1
    CRUISE = 2
    DECEL_TO_ZERO = 3
    INT_ACCEL = 4
    INT_DECEL = 5
    NA = 6

    speed = 'PID_SPEED (km/h)'
    tesla_speed_pid = 'PID_TESLA_REAR_DRIVE_UNIT_TORQUE_STATUS (vehicleSpeed km/h)'
    fms_cc_speed = 'FMS_CRUISE_CONTROL_VEHICLE_SPEED (km/h)'
    fms_tac = 'FMS_TACOGRAPH (km/h)'
    bustech_speed = 'BUSTECH_ENGINE (Speed km/h):'
    _readings = []
    idx = 0
    prev = None
    for i in readings:
        if speed not in i:
            # set the PID_SPEED km/h from the data we have
            if tesla_speed_pid in i and i[tesla_speed_pid] is not None:
                speed = tesla_speed_pid
            elif fms_cc_speed in i and i[fms_cc_speed] is not None and i[fms_cc_speed] < 200:
                speed = fms_cc_speed
            elif fms_tac in i and i[fms_tac] is not None and i[fms_tac] < 200:
                speed = fms_tac
            elif bustech_speed in i and i[bustech_speed] is not None and i[bustech_speed] < 200:
                speed = bustech_speed
            else:
                speed = 'spd_over_grnd'
        if i[speed] is not None:
            i['speed'] = round(i[speed], 2)
            i['idx'] = "{} - {}".format(idx, speed.split(' ')[0][4:16])
            i['_idx'] = idx
            idx += 1
            i.update(calc_extra(i, prev))
            prev = i
            _readings.append(i)

    readings[:] = _readings
    speed = 'speed'

    def smooth():
        it = enumerate(readings)
        next(it)
        for idx, i in it:
            try:
                prev, curr, post, post2 = readings[idx-1:idx+3]
                avg = np.mean([prev[speed], post2[speed]])
                if abs(prev[speed] - curr[speed]) > 25:
                    curr[speed] = avg
                # if abs(curr[speed] - avg) > 25 and abs(post[speed] - avg) > 25:
                #     curr[speed] = avg
                #     post[speed] = avg
            except (IndexError, ValueError) as e:
                # print(e)
                pass

    def check_next_5(start, up=1, s=1):
        try:
            return all([readings[start][speed] <= readings[start + up * 1][speed],
                        readings[start][speed] < readings[start + up * 2][speed] + (s * 0.5),
                        readings[start][speed] < readings[start + up * 3][speed] + (s * 1.0),
                        readings[start][speed] < readings[start + up * 4][speed] + (s * 1.5),
                        readings[start][speed] < readings[start + up * 5][speed] + (s * 2.0)])
        except IndexError:
            return False

    def idle_pass():
        # do Idle pass
        for i in readings:
            if abs(i[speed]) <= 2:
                i[phase] = IDLE
            else:
                i[phase] = NA

    def accel_from_stop():
        # do accel from stop
        acc_start = False
        use_phase = 1
        for idx, i in enumerate(readings):
            prev = readings[idx - 1]
            if not acc_start and i[phase] != 0 and prev[phase] == 0:
                acc_start = True
                if prev[speed] <= 2:
                    use_phase = ACCEL_FROM_ZERO
                else:
                    use_phase = INT_ACCEL
                prev[phase] = use_phase
            if acc_start:
                i[phase] = use_phase
                # check if we've reached peak accel
                if check_next_5(idx, -1, 1):  # readings[idx +1][speed] <= i[speed]:
                    acc_start = False
                    # mark the previous 5 as 0
                    for r in range(idx, idx - 5, -1):
                        readings[r][phase] = 0

                        # if i[phase] == 1:
                        #     found_start_idle = True
                        # if found_start_idle and i[phase] != 1:
                        #     if acc_start is None:
                        #         acc_start = idx - 1
                        #     if check_next_5(idx, -1, 1):
                        #         acc_finish = idx
                        #         #     for trips between acc_start and acc_finish, mark phase = 2:
                        #         for t in readings[acc_start:acc_finish]:
                        #             t[phase] = 2
                        #         acc_finish = None
                        #         acc_start = None

    def decel_to_stop():
        decc_start = False
        use_phase = DECEL_TO_ZERO
        for idx, i in enumerate(readings[-2::-1]):

            idx = len(readings) - idx - 1
            prev = readings[idx]
            if not decc_start and i[speed] > 0 and prev[phase] == 0:
                decc_start = idx
                if prev[speed] <= 2:
                    use_phase = DECEL_TO_ZERO
                else:
                    use_phase = INT_DECEL
                continue
            if decc_start:
                i[phase] = use_phase

                # check if we've reached peak decel
                if all([
                    i[speed] >= readings[idx - 2][speed],
                    i[speed] > readings[idx - 3][speed] - 0.5,
                    i[speed] > readings[idx - 4][speed] - 1,
                    i[speed] > readings[idx - 5][speed] - 1.5,
                    i[speed] > readings[idx - 6][speed] - 2,
                ]):  # readings[idx +1][speed] <= i[speed]:
                    decc_start = False
                    # mark the previous 5 as 0
                    for r in range(idx, decc_start):
                        if readings[r][phase] != 0:
                            readings[r][phase] = use_phase

    def avgStdSpeed(l):
        speeds = pluck(l, speed)
        return np.mean(speeds), np.std(speeds)

    def cruise():
        for idx, i in enumerate(readings):
            if i[speed] >= 2:
                stack = readings[idx:idx + 5]
                avg, std = avgStdSpeed(stack)
                if all(map(lambda x: abs(x[speed] - avg) < 1, stack)):
                    for j in stack:
                        j[phase] = CRUISE

    def accel_decel():

        # classify intermediate accel decel
        tStart = 0
        tk = 0
        tEnd = 0
        tMin = 0
        tMax = 0
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
                if readings[tStart][speed] < readings[tk][speed]:
                    pass
                    # for j in range(tk, tStart, -1):
                    #     if check_next_5(j, -1, 1):
                    #         tStart = j
                    #         break
                    # for j in range(tk, len(readings)):
                    #     if check_next_5(j, -1, 1):
                    #         tEnd = j
                    #         break
                    # if readings[tEnd][phase] == 0:
                    #     if readings[tEnd][speed] - readings[tStart][speed] > 10.0:
                    #         for j in range(tStart, tEnd):
                    #             readings[j][phase] = 4
                else:
                    for j in range(tk, tStart, -1):
                        if check_next_5(j, -1, -1):
                            tStart = j
                            break
                    for j in range(tk, len(readings)):
                        if check_next_5(j, 1, 1):
                            tEnd = j
                            break
                    if readings[tEnd][phase] == 0:
                        if readings[tStart][speed] - readings[tEnd][speed] > 10.0:
                            while readings[tStart][phase] != 0:
                                tStart += 1
                            for j in range(tStart, tEnd):
                                readings[j][phase] = 5
                tStart = tEnd

    # def int_decel():

    # def cruise_error_filter():
    #     j = 1
    #     duration_limit = 4
    #     for i in range()
    def cleanup():
        for idx, i in enumerate(readings):
            try:
                if i[speed] <= 2 and i['phase'] not in [DECEL_TO_ZERO, ACCEL_FROM_ZERO]:
                    i['phase'] = IDLE
                prev = readings[idx - 1]
                curr = readings[idx]
                post = readings[idx + 1]

                # if prev[phase] == post[phase]:
                #     i[phase] = prev[phase]
                # if i[phase] == 0 and i[speed] > 3:
                #     i[phase] = prev[phase]
            except IndexError:
                pass
        for idx, phase_group in enumerate(
                [(key, list(group)) for key, group in (groupby(readings, key=lambda x: x[phase]))]):
            phase_id = phase_group[0]
            p = phase_group[1]
            # print(phase_id, p)
            # continue
            if (p[-1]['timestamp'] - p[0]['timestamp']).total_seconds() < min_phase_time:
                # rejoin this phase to the previous phase
                # print("Short phase at", phase_id)
                for reading in p:
                    readings[reading['_idx']][phase] = readings[p[0]['_idx'] - 1][phase]

    # def cruise():
    #     duration_limit = 4
    #
    #     # for i in readings:
    #     #     if i[phase] == 6:
    #     #         pass
    #     c_start = None
    #     for idx, i in enumerate(readings):
    #         if i[phase] == 0 and i[speed] > 5:
    #             i[phase] = 2
    smooth()
    idle_pass()
    accel_from_stop()
    decel_to_stop()
    # accel_decel()
    cruise()
    cleanup()
    return speed


def _classify_readings_with_phases(readings):
    """
    Classify readings with the following schema:
        0. Idle at 0
        1. Acceleration from 0
        2. Cruise
        3. Deceleration to 0
        4. Intermediate acceleration
        5. Intermediate deceleration
        6. N/A
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
