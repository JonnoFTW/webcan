#!/usr/bin/env python
from multiprocessing import Pool

import pytz
from bson import CodecOptions
from pluck import pluck
from pymongo import MongoClient
import configparser
from webcan.reports import per_phase_report, _classify_readings_with_phases_pas
from webcan.utils import calc_extra
from webcan.utils.fuel_consumption_report import parse


def make_phase_report(_trip_key, uri):
    print("Start", _trip_key)
    rpi_readings = get_readings(uri)
    readings = list(rpi_readings.find({'trip_key': _trip_key}))
    readings.sort(key=lambda x: x['trip_sequence'])
    prev = None
    for i in readings:
        i.update(calc_extra(i, prev))
        prev = i
    _classify_readings_with_phases_pas(readings, 3, 1)
    phase_report = per_phase_report(readings)
    for pr in phase_report:
        for k, v in pr.items():
            pr[k] = parse(v)
    return {
        'trip_key': _trip_key,
        'vid': readings[0]['vid'],
        'phases': phase_report
    }


def get_readings(uri):
    conn = MongoClient(uri)
    return conn['webcan']['rpi_readings'].with_options(
        codec_options=CodecOptions(tz_aware=True, tzinfo=pytz.timezone('Australia/Adelaide')))


def main():
    """
     for each distinct trip_key,
     add to webcan.trip_phase
     with doc:
     {
        trip_key: ...,
        vid: adl_metro_...,
        phases: [{
            phase_no: 1,
            start:
            finish
            duration
            dist
            Start Speed (km/h)
            Finish Speed (km/h)
            Min Speed (km/h)
            Max Speed (km/h)
            Mean Speed (km/h)
            STDEV Speed (km/h)
            Coeff Beta (km/h)/√(Δt)
            Y Intercept (km/h)
            r_squared_value
            Min Acc ((Δkm/h)/s)
            Max Acc ((Δkm/h)/s)
            Mean Acc ((Δkm/h)/s)
            Total Acc ((Δkm/h)/s)
            STDEV Acc ((Δkm/h)/s)
            Total Fuel (ml)
            Min Fuel rate (L/h)
            Max Fuel Rate (L/h)
            Mean Fuel Rate (L/h)
            STDEV Fuel Rate (L/h)
            Mean CO2 (g)
            STDEV CO2 (g)
            Min Energy (kWh)
            Max Energy (kWh)
            Mean Energy (kWh)
            STDEV Energy (kWh)
        }]
     }
    """
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']
    conn = MongoClient(uri)
    trip_phase = conn['webcan']['trip_phase']
    trip_summary = conn['webcan']['trip_summary']
    rpi_readings = get_readings(uri)
    done_trips = pluck(trip_phase.find({}, {'_id': 0, 'trip_key': 1}), 'trip_key')
    trips_to_do = set(rpi_readings.distinct('trip_key')) - set(done_trips)
    trips_to_do.remove(None)

    def done(res):
        try:
            trip_summary.update({'trip_key': res['trip_key']}, {
                '$set': {
                    'phases': res['phases']
                }
            })
            print("Done", res['trip_key'])
        except Exception as e:
            # print(res)
            exit(e)

    pool = Pool(8)
    for trip_key in trips_to_do:
        pool.apply_async(make_phase_report, args=(trip_key, uri), callback=done, error_callback=print)
    pool.close()
    pool.join()
    print("Done")


if __name__ == "__main__":
    main()
