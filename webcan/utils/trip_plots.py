import configparser
from itertools import cycle

import numpy as np
from collections import defaultdict
from matplotlib import cm
from pluck import pluck
from pymongo import MongoClient


def main():
    import matplotlib.pyplot as plt

    # get all the bus data
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    conn = MongoClient(uri)['webcan']
    filtered_trips = pluck(conn.webcan_trip_filters.find(), 'trip_id')
    # vid_re = '^adl_metro_1905'

    query = {
        # 'vid': {'$in': ['adl_metro_1905','adl_metro_1901', 'adl_metro_2451', 'adl_metro_2450']},
        'Distance (km)': {'$gte': 5}
    }
    if filtered_trips:
        query['trip_id'] = {'$nin': filtered_trips}
    data = list(conn['trip_summary'].find(query))
    series = defaultdict(lambda: {'x': [], 'y': []})
    xf = 'Total Fuel (ml)'
    yf = 'Total CO2e (g)'
    for trip_summary in data:
        fuel_litres = trip_summary[xf] * 0.001
        dist_100km = trip_summary['Distance (km)'] / 100.
        fuel_usage_rate_per_100km = fuel_litres / dist_100km
        series[trip_summary['vid']]['x'].append(fuel_usage_rate_per_100km)
        series[trip_summary['vid']]['y'].append(trip_summary[yf])

    colors = cm.rainbow(np.linspace(0, 1, len(series)))
    it = cycle(colors)
    for vid, xy in series.items():
        x, y = np.array(xy['x']), np.array(xy['y'])
        color = next(it)
        plt.scatter(x, y, label="{} ({})".format(vid, len(y)), color=color)

    plt.legend()
    plt.xlabel(xf)
    plt.ylabel(yf)
    allys = np.array(sum((vals['y'] for vals in series.values()), []))
    plt.title("{} vs {} n={}".format(
        xf,
        yf,
        allys.size
    ))
    plt.show()


if __name__ == "__main__":
    main()
