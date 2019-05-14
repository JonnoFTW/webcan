import configparser
import numpy as np
from pymongo import MongoClient
import tabulate
import matplotlib.pyplot as plt


def main():
    # get all the bus data
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    conn = MongoClient(uri)['webcan']

    buses = [
        # 'adl_metro_1902',
        # 'adl_metro_1905',
        # 'adl_metro_2450',
        # 'adl_metro_2451',
        'adl_metro_2452',
    ]
    duration = 'Duration (s)'
    co2 = 'Total CO2 (g)'
    table = []
    for bus in buses:
        summaries = conn['trip_summary'].find({'vid': bus, 'Distance (km)': {'$gte': 5}})
        idle_durations = []
        idle_co2s = []
        for s in summaries:
            phases = s['phases']
            for p in phases:
                if p['phasetype'] == 0 and p[duration] > 4:
                    idle_durations.append(p[duration])
                    idle_co2s.append(p[co2] / p[duration])
        idle_durations = np.array(idle_durations)
        idles = idle_durations[np.where(idle_durations < 400)]
        plt.figure()
        n, bins, patches = plt.hist(idles,
                                    bins=range(int(min(idles)), int(max(idles)) + 5, 5),
                                    label=bus)
        plt.xlabel(duration)
        plt.ylabel('Frequency')
        plt_title = 'Histogram of Idle Phase Durations for ' + bus
        plt.title(plt_title)

        plt.savefig('./out/' + plt_title + '.png')
        table.append({
            'bus': bus,
            'Median CO2e (g) / s': np.median(idle_co2s)
        })

    print(tabulate.tabulate(table, headers='keys'))
    plt.show()


if __name__ == "__main__":
    main()
