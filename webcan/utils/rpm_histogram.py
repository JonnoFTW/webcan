from matplotlib import pyplot as plt
import configparser
import numpy as np
import json
from pymongo import MongoClient

rpm = 'FMS_ELECTRONIC_ENGINE_CONTROLLER_1 (RPM)'


def plot():
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
    boundaries = [1] + np.arange(0, 2500, 25)[1:].tolist()

    for bus in buses:
        trips = [s['trip_key'] for s in conn['trip_summary'].find({'vid': bus, 'Distance (km)': {'$gte': 5}},
                                                                  {'trip_key': 1})]
        print("Histogram of", bus)
        readings = conn['rpi_readings'].aggregate([
            {
                "$match": {
                    "vid": bus,
                    'trip_key': {'$in': trips},
                    "FMS_ELECTRONIC_ENGINE_CONTROLLER_1 (RPM)": {
                        "$exists": True
                    }
                }
            },
            {
                "$bucket": {
                    "groupBy": "$FMS_ELECTRONIC_ENGINE_CONTROLLER_1 (RPM)",
                    "boundaries": boundaries,
                    "default": "Error"
                }
            }
        ], allowDiskUse=True
        )
        # plt.figure()
        # plt.hist()
        counts = {x: 0 for x in boundaries}
        for r in readings:
            try:
                counts[int(r['_id'])] = r['count']
            except:
                counts[0] = r['count']
        with open('./out/' + bus + '_histogram.json', 'w') as outf:
            json.dump(counts, outf)
        with open('./out/' + bus + '_histogram.csv', 'w') as outf:
            outf.write("bin,count\n")
            for b, c in sorted(counts.items()):
                outf.write("{},{}\n".format(b, c))
        # del counts['Error']
        # val, weight = zip(*[(k, v) for k, v in counts.items()])

        # plt.hist(val, weights=weight)
        # plt.title("RPM Histogram for " + bus)
        # plt.xlabel("RPM")
        # plt.ylabel("Frequency")
    plt.show()


if __name__ == "__main__":
    plot()
