from itertools import groupby
import configparser
import numpy as np
from pluck import pluck
from scipy import stats
from pymongo import MongoClient
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

from webcan.reports import _classify_readings_with_phases_pas
from webcan.utils import calc_extra

plt.rcParams["figure.figsize"] = (14, 10)


def trend_lbl(name, length, slope, intercept, r_value):
    return "{} ({})\n$y={}x+{}$\n$r^2$={}".format(name, length, np.round_(slope, 3), np.round_(intercept, 3),
                                                  np.round(r_value, 3))


def plot(x_title,
         y_title,
         plt_title,
         # xlim,
         # ylim
         ):
    # get all the bus data
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']
    conn = MongoClient(uri)['webcan']

    bus = 'adl_metro_1999'

    readings_col = conn['rpi_readings']
    trip_key = conn['trip_summary'].find_one({'vid': bus, 'Distance (km)': {'$gte': 5}})['trip_key']

    readings = []
    for _r in readings_col.find({
        'trip_key': trip_key,
        'vid': bus,

    }):
        # filter out the garbage
        rpm = _r.get('FMS_ELECTRONIC_ENGINE_CONTROLLER_1 (RPM)')
        if rpm is not None and rpm > 8000:
            continue
        else:
            readings.append(_r)

    readings.sort(key=lambda r: r['trip_sequence'])
    prev = None
    for p in readings:
        p.update(calc_extra(p, prev))
        prev = p

    _classify_readings_with_phases_pas(readings, 3, 1)
    accel_phases = []
    for g, vals in groupby(readings, key=lambda x: x['phase']):
        vals = list(vals)

        if g == 1 and (vals[-1]['timestamp'] - vals[0]['timestamp']).total_seconds() > 5:
            accel_phases.append(vals)

    # pick the an accel phase somewhere
    phase = accel_phases[0]
    x, y = [], []
    start_time = phase[0]['timestamp']
    for r in phase:
        x.append((r['timestamp'] - start_time).total_seconds())
        y.append(r['spd_over_grnd'])

    x = np.array(x)
    y = np.array(y)
    times = pluck(phase, 'timestamp')
    sqrt_x = np.sqrt([(t - times[0]).total_seconds() for t in times]),
    bus_short = bus.split('_')[-1]

    plt.figure()
    plt.scatter(x, y, s=4, label='Speed Over time')
    plt.scatter(sqrt_x, y, s=4, label='sqrt speed over time')
    trend = stats.linregress(x, y)
    slope, intercept, r_value, p_value, std_err = trend
    plt.plot(x, intercept + slope * x,
             label=trend_lbl(bus_short, len(x), slope, intercept, r_value),
             color='k',
             path_effects=[pe.Stroke(linewidth=5, foreground='r'), pe.Normal()]
             )

    # plt.ylim(*ylim)
    # plt.xlim(*xlim)
    plt.xlabel(x_title)
    plt.ylabel(y_title)
    plt.legend()
    plt.title(plt_title + bus_short)
    plt.savefig('./out/' + plt_title + bus_short + '.png')

    plt.show()


if __name__ == "__main__":
    plot("Time (s)", "Speed (km/h)", "Speed over time for Acceleration from Zero Phase for ")
