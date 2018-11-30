from itertools import cycle
import configparser
import numpy as np
from scipy import stats
from matplotlib import cm
from pymongo import MongoClient
import tabulate
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe


def trend_lbl(name, length, slope, intercept, r_value):
    return "{} ({})\ny={}x+{}\nr={}".format(name, length, np.round_(slope, 3), np.round_(intercept, 3),
                                            np.round(r_value, 3))


def plot(f, x_title, y_title, plt_title, trend_title, xlim, ylim):
    """

    :param f: function to run on each phase, returns an x and y tuple
    :param x_title:  the x axis label
    :param y_title:  the y axis label
    :param plt_title:  the plot title prefix
    :param trend_title: the trendline comparison title
    :return:
    """
    # get all the bus data
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    conn = MongoClient(uri)['webcan']

    buses = [
        'adl_metro_1902',
        'adl_metro_1905',
        'adl_metro_2450',
        'adl_metro_2451',
        # 'adl_metro_2452',
    ]
    table = []

    for bus in buses:
        summaries = conn['trip_summary'].find({'vid': bus, 'Distance (km)': {'$gte': 5}})
        x, y = [], []
        for s in summaries:
            phases = s['phases']
            for p in phases:
                out = f(p)
                if out:
                    x.append(out[0])
                    y.append(out[1])
        plt.figure()
        x = np.array(x)
        y = np.array(y)
        trend = stats.linregress(x, y)
        slope, intercept, r_value, p_value, std_err = trend
        plt.scatter(x, y, s=4)
        bus_short = bus.split('_')[-1]
        plt.plot(x, intercept + slope * x,
                 label=trend_lbl(bus_short, len(x), slope, intercept, r_value),
                 color='k',
                 path_effects=[pe.Stroke(linewidth=5, foreground='r'), pe.Normal()]
                 )
        plt.ylim(*ylim)
        plt.xlim(*xlim)
        plt.xlabel(x_title)
        plt.ylabel(y_title)
        plt.legend()
        plt.title(plt_title + bus_short)
        plt.savefig('./out/' + plt_title + bus_short + '.png')
        table.append({
            'bus': bus_short,
            'Trend': trend,
            'x': x
        })
    colors = cm.rainbow(np.linspace(0, 1, len(table)))
    it = cycle(colors)
    plt.figure()
    for row in table:
        slope, intercept, r_value, p_value, std_err = row['Trend']
        x = row['x']
        plt.plot(row['x'], intercept + slope * x,
                 label=trend_lbl(row['bus'], len(x), slope, intercept, r_value),
                 color='k',
                 path_effects=[pe.Stroke(linewidth=4, foreground=next(it)), pe.Normal()]
                 )
    plt.legend()
    plt.title(trend_title)
    plt.xlabel(x_title)
    plt.ylim(*ylim)
    plt.xlim(*xlim)

    plt.ylabel(y_title)
    plt.savefig('./out/' + trend_title + '.png')
    plt.show()
    print(trend_title)
    print(tabulate.tabulate([{f: row[f] for f in row if f != 'x'} for row in table], headers='keys'))
