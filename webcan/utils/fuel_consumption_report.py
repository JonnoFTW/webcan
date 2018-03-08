import tabulate
import configparser
from multiprocessing import Pool
import tqdm
from geopy.distance import vincenty
from pymongo import MongoClient
from pluck import pluck
from itertools import groupby
from webcan.utils import calc_extra
import numpy as np


def fuel_report_trip(trip_id, p):
    report = {'trip_id': trip_id}
    prev = None
    p.sort(key=lambda x: x['trip_sequence'])
    for r in p:
        r.update(calc_extra(r, prev))
        prev = r
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
        if fms_spd in r and '_duration' in r and r[fms_spd] < 2:
            idle_time += r['_duration']
    energy = np.array(pluck(p, 'Total Energy (kWh)', default=0))
    report.update({
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
        'FSM Mean Speed (km/h)': np.mean(speeds_fms),
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
        '% Idle': idle_time / duration * 100
    })
    return report


def main():
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    conn = MongoClient(uri)['mack0242']
    filtered_trips = pluck(conn.webcan_trip_filters.find(), 'trip_id')
    vid_re = '^adl_metro'
    num_trips = len(set(x.split('_')[2] for x in
                        conn.rpi_readings.distinct('trip_id', {'vid': {'$regex': vid_re}}))
                    - set(x.split('_')[2] for x in filtered_trips))
    # generate a fuel consumption report
    cursor = conn.rpi_readings.find(
        {'vid': {'$regex': vid_re},
         'pos': {'$exists': True},
         'trip_id': {'$nin': filtered_trips}}).sort([('trip_key', 1)])
    report = []
    prog = tqdm.tqdm(desc='Trip Reports', total=num_trips, unit=' trips')

    def on_complete(r):
        report.append(r)
        prog.update()

    pool = Pool()
    i = 0
    for trip_id, readings in groupby(cursor, key=lambda x: x['trip_key']):
        readings = list(readings)
        # on_complete(fuel_report_trip(trip_id, readings))
        pool.apply_async(fuel_report_trip, args=(trip_id, readings), callback=on_complete)
        i += 1

    pool.close()
    pool.join()
    prog.close()
    import csv
    with open('adl_metro_report_fms_speed.csv', 'w') as out:
        writer = csv.DictWriter(out, fieldnames=list(report[0].keys()))
        writer.writeheader()
        writer.writerows(report)
    print(tabulate.tabulate(report, headers='keys'))


if __name__ == "__main__":
    main()
