import pytz
import configparser
from multiprocessing import Pool
import tqdm
from bson import CodecOptions
from geopy.distance import vincenty
from pymongo import MongoClient, ASCENDING
from pluck import pluck

from webcan.reports import _classify_readings_with_phases_pas, per_phase_report
from webcan.utils import calc_extra
import numpy as np

np.seterr(all='raise')


def phase_and_summary_report(trip_key, vid, uri, exclude):
    conn = MongoClient(uri)['webcan']
    readings_col = conn.rpi_readings.with_options(
        codec_options=CodecOptions(tz_aware=True, tzinfo=pytz.timezone('Australia/Adelaide')))
    try:
        readings = []
        for _r in readings_col.find({
            'trip_key': trip_key,
            'vid': vid,
            # 'pos': {
            #     '$not': {
            #         '$geoWithin': exclude
            #     }
            # }
        }):
            # filter out the garbage
            rpm = _r.get('FMS_ELECTRONIC_ENGINE_CONTROLLER_1 (RPM)')
            if rpm is not None and rpm > 8000:
                continue
            else:
                readings.append(_r)

        readings.sort(key=lambda x: x['trip_sequence'])
        prev = None
        for p in readings:
            p.update(calc_extra(p, prev))
            prev = p

        _classify_readings_with_phases_pas(readings, 3, 1)
        phase_report = per_phase_report(readings)
    except Exception as e:
        raise Exception(f"Error reporting {vid}:{trip_key} {e}")
    for pr in phase_report:
        for k, v in pr.items():
            pr[k] = parse(v)
    summary = {
        'trip_key': trip_key,
        'vid': readings[0]['vid'],
        'phases': phase_report
    }
    p = readings
    fms_spd = 'FMS_CRUISE_CONTROL_VEHICLE_SPEED (km/h)'
    gps_spd = 'spd_over_grnd'
    duration = (p[-1]['timestamp'] - p[0]['timestamp']).total_seconds()
    speeds_fms = np.array(pluck(p, fms_spd, default=0))
    speeds = np.array(pluck(p, gps_spd, default=0))
    fuel_rates = np.array(pluck(p, 'FMS_FUEL_ECONOMY (L/h)', default=0))
    # durations = np.array(pluck(p, '_duration', default=0)) / 3600
    # fuels = fuel_rates * durations  # should be in ml

    # if not any(fuel_rates):
    #     fuel_rates = np.array(pluck(p, 'Petrol Used (ml)', default=0)) / 1000 / durations
    fuels = pluck(p, 'Petrol Used (ml)', default=0)
    co2s = pluck(p, 'Total CO2e (g)', default=0)
    idle_time = 0
    for r in p:
        if gps_spd in r and '_duration' in r and r[gps_spd] < 2:
            idle_time += r['_duration']
    energy = np.array(pluck(p, 'Total Energy (kWh)', default=0))
    summary.update({
        'vid': p[0]['vid'],
        'Start Time': p[0]['timestamp'],
        'Finish Time': p[-1]['timestamp'],
        'Duration (s)': duration,
        'Idle Duration (s)': idle_time,
        'Distance (km)': sum(
            vincenty(r1['pos']['coordinates'], r2['pos']['coordinates']).kilometers for r2, r1 in zip(p, p[1:])),
        'GPS Min Speed (km/h)': np.min(speeds),
        'GPS Max Speed (km/h)': np.max(speeds),
        'GPS Mean Speed (km/h)': np.mean(speeds),
        'GPS STDEV Speed (km/h)': np.std(speeds),
        'FMS Min Speed (km/h)': np.min(speeds_fms),
        'FMS Max Speed (km/h)': np.max(speeds_fms),
        'FMS Mean Speed (km/h)': np.mean(speeds_fms),
        'FMS STDEV Speed (km/h)': np.std(speeds_fms),
        'Total Fuel (ml)': np.sum(fuels),
        'Min Fuel rate (L/h)': np.min(fuel_rates),
        'Max Fuel Rate (L/h)': np.max(fuel_rates),
        'Mean Fuel Rate (L/h)': np.mean(fuel_rates),
        'STDEV Fuel Rate (L/h)': np.std(fuel_rates),
        'Mean CO2 (g)': np.mean(co2s),
        'STDEV CO2 (g)': np.std(co2s),
        'Total CO2e (g)': np.sum(co2s),
        'Total Energy (kWh)': energy.sum(),
        '% Idle': idle_time / duration * 100,
        'Fuel Economy (L/100km)': 0
    })
    try:
        summary['Fuel Economy (L/100km)'] = (summary['Total Fuel (ml)'] / 1000.) / (summary['Distance (km)'] / 100.)
    except:
        pass
    return summary


def parse(val):
    return {
        np.int64: int,
        np.float64: float,
    }.get(type(val), lambda x: x)(val)


def main():
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']


    conn = MongoClient(uri)['webcan']
    done_trips = conn.trip_summary.distinct('trip_key')
    # get all those trip keys from rpi_readings that are not in done_trips and match the vid matches ^adl_metro
    exclusion_multipolygon = {
        'type': "MultiPolygon",
        'coordinates': []
    }
    for i in conn.polygons.find({'exclude': True}):
        exclusion_multipolygon['coordinates'].append([i['poly']['coordinates']])
    trip_keys = conn.rpi_readings.distinct('trip_key',
                                           {'trip_key': {'$nin': done_trips}, 'vid': {'$regex': '^adl_metro'}})

    prog = tqdm.tqdm(trip_keys, desc='Trip Reports: ', unit=' trips')

    def on_complete(r):
        # put this in the db
        # print(r)
        try:
            conn.trip_summary.insert_one({k: parse(v) for k, v in r.items()})
        except Exception  as e:
            print("Failed to upload trip {}: {}".format(r['trip_key'], e))
        prog.update()

    pool = Pool(2)
    i = 0

    for trip_key in trip_keys:
        vid = conn.rpi_readings.find_one({'trip_key': trip_key})['vid']
        # on_complete(phase_and_summary_report(trip_key, vid, uri))
        pool.apply_async(phase_and_summary_report, args=(trip_key, vid, uri, exclusion_multipolygon), callback=on_complete,
                         error_callback=print)
        i += 1

    pool.close()
    pool.join()
    prog.close()


if __name__ == "__main__":
    main()
