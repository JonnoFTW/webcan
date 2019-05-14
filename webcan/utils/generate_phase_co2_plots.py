import configparser
from itertools import cycle

import numpy as np
from collections import defaultdict
from scipy import stats
from matplotlib import cm
from pluck import pluck
from pymongo import MongoClient
import matplotlib.patheffects as pe

def set_axlims(series, marginfactor):
    """
    Fix for a scaling issue with matplotlibs scatterplot and small values.
    Takes in a pandas series, and a marginfactor (float).
    A marginfactor of 0.2 would for example set a 20% border distance on both sides.
    Output:[bottom,top]
    To be used with .set_ylim(bottom,top)
    """
    minv = series.min()
    maxv = series.max()
    datarange = maxv-minv
    border = abs(datarange*marginfactor)
    maxlim = maxv+border
    minlim = minv-border

    return minlim, maxlim

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
        'vid': {'$in': [
            # 'adl_metro_1902',
            # 'adl_metro_1905',
            # 'adl_metro_2450',
            # 'adl_metro_2451',
            'adl_metro_2452',
        ]},
        'Distance (km)': {'$gte': 5}
    }
    if filtered_trips:
        query['trip_id'] = {'$nin': filtered_trips}
    data = list(conn['trip_summary'].find(query))
    charts = [{
            'x': 'Coeff Beta (km/h)/√(Δt)',
            'y': 'Mean Energy (kWh)',
            'phasetype': 1
        },
        {
            'x': 'Coeff Beta (km/h)/√(Δt)',
            'y': 'Total CO2 (g) `div` Duration (s)',
            'phasetype': 1
        },
        {
            'x': 'Coeff Beta (km/h)/√(Δt)',
            'y': 'Mean Energy (kWh)',
            'phasetype': 3
        },
        {
            'x': 'Mean Speed (km/h)',
            'y': 'Mean Energy (kWh)',
            'phasetype': 2
        },
    ]

    for params in charts:

        fig = plt.figure()
        series = defaultdict(lambda: dict(x=[], y=[]))
        for summary in data:
            summary_of_phase = [s for s in summary['phases'] if
                                s['phasetype'] == params['phasetype'] and s[params['y']] != 0]
            for f in 'xy':
                series[summary['vid']][f].extend(pluck(summary_of_phase, params[f]))
        colors = cm.rainbow(np.linspace(0, 1, len(series)))
        it = cycle(colors)
        for vid, xy in series.items():
            x, y = np.array(xy['x']), np.array(xy['y'])
            color = next(it)
            plt.scatter(x, y, label="{} ({})".format(vid, len(y)), color=color)
        for vid, xy in series.items():
            x, y = np.array(xy['x']), np.array(xy['y'])
            color = next(it)
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                # stats.poly
                plt.plot(x, intercept + slope * x,
                         label="{} ({})\ny={}x+{}".format(vid, len(y), np.round_(slope,3), np.round_(intercept,3)),
                         color='k',
                         path_effects=[pe.Stroke(linewidth=5, foreground=color), pe.Normal()]
                         )
            except ValueError as e:
                print("Skipping trend for ",vid)
        plt.legend()
        plt.xlabel(params['x'])
        plt.ylabel(params['y'])
        allys = np.array(sum((vals['y'] for vals in series.values()), []))
        plt.ylim(*set_axlims(allys, 0.1))
        plt.title("{} vs {} phase={} n={}".format(
            params['x'],
            params['y'],
            params['phasetype'],
            allys.size
        ))
    plt.show()


if __name__ == "__main__":
    main()
