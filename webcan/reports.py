import json
from datetime import datetime
import pytz
from pyramid.renderers import render_to_response, get_renderer
from bson.codec_options import CodecOptions

from webcan.errors import AJAXHttpBadRequest
from .utils import calc_extra
from .views import get_device_trips_for_user, _get_user_devices_ids
from pyramid.view import view_config
from geopy.distance import vincenty
from collections import defaultdict
from pluck import pluck
import numpy as np
import pymongo
from webob import exc
from itertools import groupby, zip_longest
from scipy import stats
from multiprocessing import Pool

# import asyncio
# import websockets

phase = 'phase'
trip_sequence = 'trip_sequence'
SORT_TRIP_SEQ = [('trip_id', pymongo.ASCENDING),
                 ('trip_sequence', pymongo.ASCENDING)]


@view_config(route_name='report_list', renderer="templates/reports/list_reports.mako")
def report_list(request):
    introspector = request.registry.introspector
    reports = set([
        i for i in introspector._categories['routes'].values() if
        i['pattern'].startswith('/report/') and '{' not in i['pattern'] and '/_' not in i['pattern']
    ])
    return {'reports': reports}


@view_config(route_name='report_phase', request_method='GET', renderer="templates/reports/phase_classify.mako")
def phase_classify(request):
    return {
        'trips': get_device_trips_for_user(request),
        'docs': _classify_readings_with_phases_pas.__doc__,
        'GET_TRIP': request.GET.get('trip_id', '')
    }


@view_config(route_name='report_summary', request_method='GET', renderer='templates/reports/summary_report.mako')
def summary_report(request):
    """
    Show a form where you can enter your
    """
    return {}


def summarise_trip(trip_id, readings):
    trip_report = dict(trips=0, distance=0, time=0)

    readings.sort(key=lambda x: x['trip_sequence'])
    trip_report['distance'] += sum(
        vincenty(r1['pos']['coordinates'], r2['pos']['coordinates']).kilometers for r2, r1 in
        zip(readings, readings[1:]))
    trip_report['trips'] += 1
    trip_report['time'] += (readings[-1]['timestamp'] - readings[0]['timestamp']).total_seconds()
    return trip_report, trip_id


@view_config(route_name='report_fuel_consumption_histogram', request_method='GET',
             renderer='templates/reports/fuel_report.mako')
def fuel_consumption(request):
    return {}


@view_config(route_name='report_phase_plot', request_method='GET', renderer='templates/reports/phase_plots.mako')
def phase_plot(request):
    fields = request.db.trip_summary.find_one({'$where': 'this.phases.length>0'})['phases'][0].keys()
    return {'fields': fields}


@view_config(route_name='report_phase_plot', request_method='POST', renderer='bson')
def phase_plot_render(request):
    # get the requested vehicle/trips from trip_summary
    vids = request.POST.getall('vid[]')
    query = {'Distance (km)': {'$gte': 5}, 'phases': {'$exists': True}}
    if vids:
        query['vid'] = {'$in': vids}
    # x = request.POST['x']
    # y = request.POST['y']
    phases = request.POST.getall('phases[]')
    # print(query)
    # print(request.POST)
    trips = list(request.db.trip_summary.find(query))
    fields = trips[0]['phases'][0].keys()
    out = [fields]
    for t in trips:
        for phase in t['phases']:
            if phase['phasetype'] in [int(p) for p in phases]:
                out.append([phase[f] for f in fields])
    return out


@view_config(route_name='report_trip_summary', request_method='GET',
             renderer='templates/reports/fuel_consumption_table.mako')
def fuel_consumption_all(request):
    row = request.db.trip_summary.find_one({'vid': {'$in': _get_user_devices_ids(request)}}, {'_id': 0, 'phases': 0})
    return {'row': row, 'json': json}


@view_config(route_name='trip_summary_json', request_method='GET', renderer='bson')
def trip_summary_json(request):
    heading = "Fuel Economy (L/100km)"
    rows = {
        'data': list(request.db.trip_summary.find({
            'vid': {'$in': _get_user_devices_ids(request)}
        },
            {'_id': 0, 'phases': 0}))}
    for r in rows['data']:
        if heading not in r:
            r[heading] = r['Total Fuel (ml)'] / 1000. / r['Distance (km)'] / 100.
    return rows


def trip_dist_fuel(lreadings, trip_key):
    print("Doing trip:", trip_key)
    dist = 0
    fuel_usage = 0
    prev = None
    for r in lreadings:
        r.update(calc_extra(r, prev))
        fuel_usage += r.get('Petrol Used (ml)', 0)
        if prev is not None:
            dist += vincenty(r['pos']['coordinates'], prev['pos']['coordinates']).kilometers
        prev = r
    return dist, fuel_usage, trip_key


@view_config(route_name='report_fuel_consumption_histogram', request_method='POST', renderer="json")
def fuel_consumption_render(request):
    """
    Get the data for all trips of this vehicle longer than given distance
    Calculate total fuel usage in L, divide by 100km done to get L/100km,
    return the list of trips -> fuel rate
    :param request:
    :return:
    """

    min_trip_distance = float(request.POST.get('min_trip_distance', 5))
    device_ids = request.POST.getall('device[]')

    out = [device_ids]
    tables = defaultdict(list)
    labels = defaultdict(list)

    def merge(res, dev_id):
        dist, fuel_usage, trip_key = res
        fuel_litres = fuel_usage * 0.001
        dist_100km = dist / 100.
        fuel_usage_rate_per_100km = fuel_litres / dist_100km
        # suffix = "{} {}km {} mL {} L/100km".format(trip_key, dist, fuel_usage, fuel_usage_rate_per_100km)
        # if dist >= min_trip_distance:
        tables[dev_id].append(fuel_usage_rate_per_100km)
        labels[dev_id].append(trip_key)
        # out.append([trip_key, fuel_usage_rate_per_100km])
        # print("Accepted", suffix)
        # else:
        #     print("Rejected", suffix)

    data = {}

    for device_id in device_ids:
        out = [device_ids]
        ignored = list(x['trip_id'].split('_')[2] for x in request.db.webcan_trip_filters.find({'vid': device_id}))
        for trip_summary in request.db.trip_summary.find({'vid': device_id,
                                                          'trip_key': {'$nin': ignored},
                                                          'Distance (km)': {'$gte': min_trip_distance},
                                                          'Fuel Economy (L/100km)': {'$gt': 1, '$lt': 100}
                                                          },
                                                         {'_id': 0, 'phases': 0}):
            # if cached is None:
            #     skipped.append(trip_key)
            #
            #     # readings = list(request.db.rpi_readings.find({'trip_key': trip_key}))
            #     # pool.apply_async(trip_dist_fuel, args=(readings, trip_key), callback=merge, error_callback=print)
            # else:
            merge((trip_summary[f] for f in ('Distance (km)', 'Total Fuel (ml)', 'trip_key')), device_id)
        fuel_usages = np.array(tables[device_id]).astype(np.float)
        data[device_id] = {
            'n': fuel_usages.size,
            'std': str(round(np.std(fuel_usages), 2)),
            'mean': str(round(np.mean(fuel_usages), 2))
        }
    out.extend(zip_longest(*(tables[x] for x in device_ids)))
    data['table'] = out
    data['labels'] = labels
    return data


@view_config(route_name='trip_summary_info', request_method='GET', renderer='bson')
def trip_summary_info(request):
    trip_key = request.matchdict['trip_key']
    return request.db.trip_summary.find_one({'trip_key': trip_key}, {'phases': 0, '_id': 0, 'trip_key': 0})


@view_config(route_name='show_summary_exclusions', request_method='GET',
             renderer='templates/reports/summary_exclusions.mako')
def show_excludes(request):
    return {}


@view_config(route_name='show_summary_exclusions', request_method='POST', renderer='bson')
def get_exclude_polys(request):
    polys = list(request.db.polygons.find({},{'_id':0}))
    return {'polys': polys}


@view_config(route_name='report_summary', request_method='POST', renderer='bson')
def summary_report_do(request):
    min_trip_distance = float(request.POST.get('min-trip-distance', 5))
    excluded = []

    def gen_summary_report_for_vehicle(vid):
        # get all distinct trip_keys for this vehicle
        # trip_keys = list([x.split('_')[2] for x in request.db.rpi_readings.distinct('trip_id', {'vid': vid})])
        # get all the trip_summary data, if not exists, generate
        report = dict(trips=0, distance=0, time=0, first=datetime(9999, 1, 1), last=datetime(2000, 1, 1))
        report['vehicle'] = request.db.webcan_devices.find_one({'name': vid},{'_id':0, 'secret': 0})
        def merge(trip_info):
            x, trip_id = trip_info
            if x['distance'] >= min_trip_distance:
                for k, v in x.items():
                    report[k] += v
            else:
                excluded.append(trip_id)

        filtered_trips = pluck(request.db.webcan_trip_filters.find({'vid': vid}), 'trip_id')
        pool = Pool()
        query = {'vid': vid, 'trip_key': {'$nin': filtered_trips},
                 'Distance (km)': {'$gte': min_trip_distance},
                 'Fuel Economy (L/100km)': {'$gt': 1, '$lt': 100}}
        vehicle_obj = request.db.webcan_devices.find_one({'name': vid})
        if vehicle_obj is not None and vehicle_obj['type'] == 'Electric':
            del query['Fuel Economy (L/100km)']
        for trip_summary in request.db.trip_summary.find(query, {'phases': 0}):
            # if trip_summary is None:
            #     cursor = request.db.rpi_readings.find({
            #         'vid': vid,
            #         'trip_id': {'$nin': filtered_trips}
            #     }, {'_id': False}).sort('trip_key', 1)
            #     trips = groupby(cursor, lambda x: x['trip_key'])
            #     print("Doing summary for", trip_key)
            #     for trip_id, readings in trips:
            #         # summarise_trip(trip_id, list(readings), report)
            #         lreadings = list(readings)
            #         report['first'] = min(lreadings[0]['timestamp'], report['first'])
            #         report['last'] = max(lreadings[-1]['timestamp'], report['last'])
            #         pool.apply_async(summarise_trip, args=(trip_id, lreadings), callback=merge, error_callback=print)
            # else:
            report['first'] = min(trip_summary['Start Time'], report['first'])
            report['last'] = max(trip_summary['Finish Time'], report['last'])
            # print("Used cached", trip_key)
            ts = {
                'trips': 1,
                'distance': trip_summary['Distance (km)'],
                'time': trip_summary['Duration (s)']
            }
            merge((ts, trip_summary['trip_key']))
        pool.close()
        pool.join()
        return report

    """
    Summary is a dict of
    vehicle_id: {
        'trips': int,
        'distance': float,
        'time': float,
        'petrol_used': float
    }
    """
    summary = {}

    # group everything by trip_id
    vids = request.POST.getall('devices[]')
    if not vids:
        return exc.HTTPBadRequest('Please enter at least 1 vehicle')
    for vid in vids:
        summary[vid] = gen_summary_report_for_vehicle(vid)
    # print(summary)
    vals = list(summary.values())
    summary['Aggregate'] = {key: sum(pluck(vals, key)) for key in ['trips', 'distance', 'time']}
    summary['Aggregate']['last'] = max(pluck(vals, 'last'))
    summary['Aggregate']['first'] = min(pluck(vals, 'first'))
    return {'summary': summary, 'excluded': excluded}


@view_config(route_name='report_phase', request_method='POST', renderer="bson")
def phase_classify_render(request):
    query = {
        'timestamp': {'$exists': True, '$ne': None}
    }
    # print(request.POST)
    min_phase_time = float(request.POST.get('min-phase-seconds'))
    cruise_window = float(request.POST.get('cruise-window'))
    if request.POST.getall('trips[]'):
        query['trip_id'] = {'$in': request.POST.getall('trips[]')}
    else:
        query['trip_id'] = {
            '$nin': pluck(request.db.webcan_trip_filters.find({'vid': {'$in': request.POST.getall('devices[]')}}),
                          'trip_id')
        }
    if request.POST.getall('devices[]'):
        query['vid'] = {'$in': request.POST.getall('devices[]')}
    readings = request.db.rpi_readings.with_options(
        codec_options=CodecOptions(tz_aware=True, tzinfo=pytz.timezone('Australia/Adelaide')))
    cursor = readings.find(query, {'_id': False}).sort(SORT_TRIP_SEQ)
    print(query)
    print("Len readings:", cursor.count())
    readings = list(cursor)
    speed = _classify_readings_with_phases_pas(readings, min_phase_time, cruise_avg_window=cruise_window)
    summary = _summarise_readings(readings)
    return {
        'readings': readings,
        # 'readings': [],
        'summary': summary,
        'speed_field': speed
    }


@view_config(route_name='report_phase_for_vehicle', request_method='POST', renderer="csv")
def phase_classify_csv_render(request):
    query = {
        # 'timestamp': {'$exists': True, '$ne': None},
    }

    min_phase_time = int(request.POST.get('min-phase-seconds'))
    cruise_window = int(request.POST.get('cruise-window'))
    if request.POST.get('select-trips'):
        query['trip_id'] = {'$in': request.POST.get('select-trips').split(',')}
    else:
        query['trip_id'] = {
            '$nin': pluck(
                request.db.webcan_trip_filters.find({'vid': {'$in': request.POST.get('select-trips').split(',')}}),
                'trip_id')
        }
    if request.POST.get('select-vids'):
        query['vid'] = {'$in': request.POST.get('select-vids').split(',')}
    if any(request.POST.getall('map-hull')):
        query['pos'] = {
            '$geoWithin': {
                '$geometry': {
                    'type': 'Polygon',
                    'coordinates': request.POST.getall('map-hull')
                }
            }
        }
    print(request.POST)
    print(query)
    cursor = request.db.rpi_readings.find(query, {'_id': False}).sort(SORT_TRIP_SEQ)
    trips = groupby(cursor, lambda x: x['trip_key'])
    rows = []
    for trip_id, readings in trips:
        readings = list(readings)
        prev = None
        for i in readings:
            i.update(calc_extra(i, prev))
            prev = i
        _classify_readings_with_phases_pas(readings, min_phase_time, cruise_window)
        phase_report = per_phase_report(readings, min_phase_time)
        rows.extend(phase_report)
    if len(rows) == 0:
        raise exc.HTTPBadRequest('No data returned for query')
    headers = rows[0].keys()
    data = {
        'header': headers,
        'rows': rows,
    }
    renderer_obj = get_renderer('csv')
    request.response.content_type = renderer_obj.content_type
    request.response.content_disposition = 'attachment;filename=phase_report_{}.{}'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S'), renderer_obj.content_type.split('/')[1])
    return render_to_response(
        renderer_name='csv',
        value=data,
        request=request,
        response=request.response
    )


@view_config(route_name='trip_summary_csv', renderer='csv')
def export_trip_summary_csv(request):
    # get the trip summaries for which the user can view
    rows = list(request.db.trip_summary.find({'vid': {'$in': _get_user_devices_ids(request)}}, {'phases': 0, '_id': 0}))
    request.response.content_disposition = 'attachment;filename=trip_summary_{}.csv'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S'))
    return render_to_response(
        renderer_name='csv',
        value={
            'header': rows[0].keys(),
            'rows': rows,
        },
        request=request,
        response=request.response
    )


def per_phase_report(readings, min_duration=5):
    """
    For a bunch of readings, calculate some stats about every phase it did,
    splitting up by trip_id
    :param readings:
    :return:
    """
    phases = []
    for idx, phase_group in enumerate(
            [(key, list(group)) for key, group in (groupby(readings, key=lambda x: f"{x['phase']}:{x['trip_id']}"))]):
        phase_type = phase_group[0].split(':')[0]
        phase_no = idx
        p = phase_group[1]
        duration = (p[-1]['timestamp'] - p[0]['timestamp']).total_seconds()
        if duration < min_duration:
            continue
        if len(p) < 2:
            continue
        speeds = pluck(p, 'speed')
        fuel_rates = np.array(pluck(p, 'FMS_FUEL_ECONOMY (L/h)', default=0)) / 1000
        durations = np.array(pluck(p, '_duration', default=1e-9)) / 3600
        fuels = fuel_rates * durations  # should be in ml

        if not any(fuel_rates):
            fuel_rates = np.array(pluck(p, 'Petrol Used (ml)', default=0)) / 1000 / durations
            fuels = pluck(p, 'Petrol Used (ml)', default=0)
        co2s = pluck(p, 'Total CO2e (g)', default=0)

        accels = [(s2['speed'] - s1['speed']) / ((s2['timestamp'] - s1['timestamp']).total_seconds()) for s1, s2
                  in zip(p, p[1:])]
        times = pluck(p, 'timestamp')

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            np.sqrt([(x - times[0]).total_seconds() for x in times]),
            speeds)

        energy = np.array(pluck(p, 'Total Energy (kWh)', default=0))
        phases.append({
            'phasetype': int(phase_type),
            'phase_no': phase_no,
            'trip_id': p[0]['trip_id'],
            'Start Time': p[0]['timestamp'],
            'Finish Time': p[-1]['timestamp'],
            'Duration (s)': duration,
            'Avg Temp (°C)': np.mean(pluck(p, 'FMS_ENGINE_TEMP (°C)', default=0)),
            'Distance (km)': sum(
                vincenty(r1['pos']['coordinates'], r2['pos']['coordinates']).kilometers for r2, r1 in zip(p, p[1:])),
            'Start Speed (km/h)': speeds[0],
            'Finish Speed (km/h)': speeds[-1],
            'Min Speed (km/h)': np.min(speeds),
            'Max Speed (km/h)': np.max(speeds),
            'Mean Speed (km/h)': np.mean(speeds),
            'STDEV Speed (km/h)': np.std(speeds),
            'Coeff Beta (km/h)/√(Δt)': slope,
            'Y Intercept (km/h)': intercept,
            'r_squared_value': r_value ** 2,
            # 'p_value': p_value,
            'Min Acc ((Δkm/h)/s)': np.min(accels),
            'Max Acc ((Δkm/h)/s)': np.max(accels),
            'Mean Acc ((Δkm/h)/s)': np.mean(accels),
            'Total Acc ((Δkm/h)/s)': (p[-1]['speed'] - p[0]['speed']) / duration,  # change in speed km/h
            'STDEV Acc ((Δkm/h)/s)': np.std(accels),
            'Total Fuel (ml)': np.sum(fuels),
            'Min Fuel rate (L/h)': np.min(fuel_rates),
            'Max Fuel Rate (L/h)': np.max(fuel_rates),
            'Mean Fuel Rate (L/h)': np.mean(fuel_rates),
            'STDEV Fuel Rate (L/h)': np.std(fuel_rates),
            # 'Mean NOX': 0,
            # 'STDEV NOx': 0,
            # 'Mean HC': 0,
            # 'STDEV HC': 0,
            # 'Mean CH4': 0,
            # 'STDEV CH4': 0,
            # 'Mean CO': 0,
            # 'STDEV CO': 0,
            'Mean CO2 (g)': np.mean(co2s),
            'STDEV CO2 (g)': np.std(co2s),
            'Total CO2 (g)': np.sum(co2s),
            # 'Mean FC': 0,
            # 'STDEV FC': 0,
            # 'Mean PM': 0,
            # 'STDEV PM': 0,
            # 'Mean OP': 0,
            # 'STDEV OP': 0
            'Min Energy (kWh)': energy.min(),
            'Max Energy (kWh)': energy.max(),
            'Mean Energy (kWh)': energy.mean(),
            'STDEV Energy (kWh)': energy.std(),
            'Total Energy (kWh)': energy.sum()

        })
    return phases


def seconds_2_hms(duration):
    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)
    return h, m, s


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
            phases = {"Phase {}".format(i): 0.0 for i in range(7)}
            # print(val)
            start = val[0]['timestamp']

            for r1, r2 in zip(val, val[1:]):
                if r1['trip_id'] != r2['trip_id']:
                    duration += (r1['timestamp'] - start).total_seconds()
                    start = r2['timestamp']
                    continue
                dist += vincenty(r1['pos']['coordinates'], r2['pos']['coordinates']).kilometers

            for phase, data in groupby(val, key=lambda x: f"{x['phase']}:{x['trip_key']}"):
                phase = phase.split(':')[0]
                data = list(data)
                phase_duration = (data[-1]['timestamp'] - data[0]['timestamp']).total_seconds()
                phases[f"Phase {phase}"] += phase_duration
            duration += (val[-1]['timestamp'] - start).total_seconds()
            h, m, s = seconds_2_hms(duration)
            usages = [
                'Total CO2e (g)',
                'Total Energy (kWh)',
                'Petrol Used (ml)',
                'Petrol CO2e (g)',
                'Petrol cost (c)',
                'P Used (kWh)',
                'E Used (kWh)',
                'E CO2e (g)',
                'E cost (c)',
            ]
            out[key] = {
                'Duration': "%d:%02d:%02d" % (h, m, s),
                'Distance (km)': round(dist, 4),
            }
            for field in usages:
                out[key][field] = round(sum(pluck(val, field, default=0)), 2)
            total_time = sum(phases.values())
            out[key].update({
                k: "{} ({:.2f}%)".format("{:02d}:{:02d}:{:02d}".format(*(int(x) for x in seconds_2_hms(v))),
                                         100 * v / total_time) for k, v
                in phases.items()})
            out[key]['Start'] = val[0]['timestamp'].isoformat(' ')
            out[key]['End'] = val[-1]['timestamp'].isoformat(' ')
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


def _classify_readings_with_phases_pas(readings, min_phase_time, cruise_avg_window=0.5):
    """
    0. Idle
    1. Acceleration from zero
    2. Cruise
    3. Deceleration to zero
    4. Intermediate acceleration
    5. Intermediate deceleration
    """
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
            i['speed'] = np.floor(round(i[speed]))
            i['idx'] = "{} - {}".format(idx, speed.split(' ')[0][4:16])
            i['_idx'] = idx
            if abs(i[speed]) <= 2:
                i[phase] = IDLE
            else:
                i[phase] = NA
            idx += 1
            if prev is not None and i['trip_id'] != prev['trip_id']:
                prev = None
            else:
                i.update(calc_extra(i, prev))
                prev = i
            _readings.append(i)

    readings[:] = _readings
    speed = 'speed'

    def check_next_5(start, up=1, s=1):
        try:
            return all([readings[start][speed] <= readings[start + up * 1][speed],
                        readings[start][speed] < readings[start + up * 2][speed] + (s * 0.5),
                        readings[start][speed] < readings[start + up * 3][speed] + (s * 1.0),
                        readings[start][speed] < readings[start + up * 4][speed] + (s * 1.5),
                        readings[start][speed] < readings[start + up * 5][speed] + (s * 2.0)])
        except IndexError:
            return False

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

    def accel_all():
        """
        Go through all datapoints, mark those that are increasing as accel
        if it started at idle, use ACCEL_FROM_ZERO
        else use INT_ACCEL

        :return:
        """
        stack = []
        fwds = 4
        for idx, i in enumerate(readings):
            nexts = readings[idx + 1:idx + fwds + 1]

            if len([x for x in nexts if x[speed] > i[speed]]) >= len(nexts) / 2:
                stack.append(i)
            elif stack:
                # stop and mark everything in the stack
                prev = readings[stack[0]['_idx'] - 1]
                if prev[speed] <= 2 or prev[phase] == ACCEL_FROM_ZERO:
                    use_phase = ACCEL_FROM_ZERO
                    # prev[phase] = use_phase
                else:
                    use_phase = INT_ACCEL
                for r in stack:
                    if r[speed] > 2 and r[phase] == NA:
                        r[phase] = use_phase
                        readings[r['_idx'] + 1][phase] = use_phase
                stack = []

    def decel_all():
        """
        Go through all datapoints, mark those that are decreasing as decel
        if it started at idle, use DECEL_FROM_ZERO
        else use INT_DECEL

        :return:
        """
        stack = []
        for i in readings[1:]:
            prev = readings[i['_idx'] - 1]
            if i[speed] <= prev[speed] and i[phase] != IDLE:
                stack.append(i)
            elif stack:
                # stop and mark everything in the stack
                if i[phase] == IDLE:
                    use_phase = DECEL_TO_ZERO
                    i[phase] = use_phase
                else:
                    use_phase = INT_DECEL

                # i[phase] = use_phase
                for r in stack:
                    if r[speed] >= 2 and r[phase] == NA:
                        r['phase'] = use_phase
                readings[stack[-1]['_idx'] + 1]['phase'] = use_phase
                stack = []

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
                cspd = i[speed]
                if all([
                    cspd >= readings[idx - 1][speed],
                    cspd > readings[idx - 2][speed] - 0.5,
                    cspd > readings[idx - 3][speed] - 1,
                    cspd > readings[idx - 4][speed] - 1.5,
                    cspd > readings[idx - 5][speed] - 2,
                ]):
                    if use_phase == INT_DECEL:
                        idx += 5
                    for r in range(idx, decc_start):
                        if readings[r][phase] != 0:
                            readings[r][phase] = use_phase
                    decc_start = False

    def avgStdSpeed(l):
        speeds = pluck(l, speed)
        return np.mean(speeds), np.std(speeds)

    def cruise():
        for idx, i in enumerate(readings):
            if i[speed] >= 2:
                stack = readings[idx:idx + 5]
                avg, std = avgStdSpeed(stack)
                i['_avg_spd'] = round(avg, 3)
                i['_std_spd'] = round(std, 3)
                # if i['_std_spd'] < 1:
                #     i[phase] = CRUISE
                # continue
                if all(map(lambda x: abs(x[speed] - avg) < cruise_avg_window, stack)):
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

    def cleanup():
        it = enumerate(readings)
        for idx, i in it:
            try:
                # if i[speed] <= 2 and i['phase'] not in [DECEL_TO_ZERO, ACCEL_FROM_ZERO]:
                #     i['phase'] = IDLE
                prev = readings[idx - 1]
                post = readings[idx + 1]
                if i[phase] == DECEL_TO_ZERO and post[phase] == IDLE:
                    post[phase] = DECEL_TO_ZERO
                    next(it)
                if i[phase] == IDLE and post[speed] >= 2:
                    i[phase] = ACCEL_FROM_ZERO
                    post[phase] = ACCEL_FROM_ZERO
                    next(it)
                if post[phase] == prev[phase] and i[phase] != prev[phase] or i[phase] == NA:
                    if post[phase] != NA:
                        i[phase] = post[phase]
                    else:
                        i[phase] = prev[phase]
                # if i[phase] == INT_DECEL and post[phase] != i[phase]:
                #     i[phase] = post[phase]
                # if i[phase] != post[phase] and post[phase] == prev[phase]:
                #     i[phase] = post[phase]

            except IndexError:
                pass
        # for idx, phase_group in enumerate(
        #         [(key, list(group)) for key, group in (groupby(readings, key=lambda x: x[phase]))]):
        #     phase_id = phase_group[0]
        #     p = phase_group[1]
        #     # print(phase_id, p)
        #     # continue
        #     if (p[-1]['timestamp'] - p[0]['timestamp']).total_seconds() < min_phase_time:
        #         # rejoin this phase to the previous phase
        #         # print("Short phase at", phase_id)
        #         for reading in p:
        #             readings[reading['_idx']][phase] = readings[p[0]['_idx'] - 1][phase]

    accel_all()
    decel_all()
    cruise()
    # accel_from_stop()
    # decel_to_stop()
    # accel_decel()
    cleanup()
    return speed
