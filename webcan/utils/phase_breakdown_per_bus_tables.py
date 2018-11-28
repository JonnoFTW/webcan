# tabulated count of duration number of time duration proportion
# with std dev and median, mean
#

# idle - all idle phases
# accel from idle - beta coeff
# decel from idle - decel rate
# int accel avg accel rates
# int decel avg decel rate


# by bus
import configparser
from itertools import cycle

import numpy as np
from collections import defaultdict
from scipy import stats
from matplotlib import cm
from pluck import pluck
from pymongo import MongoClient
import tabulate


def main():
    # get all the bus data
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    conn = MongoClient(uri)['webcan']
    filtered_trips = pluck(conn.webcan_trip_filters.find(), 'trip_id')
    # vid_re = '^adl_metro_1905'
    buses = [
        'adl_metro_1902',
        'adl_metro_1905',
        'adl_metro_2450',
        'adl_metro_2451',
        'adl_metro_2452',
    ]
    query = {
        'vid': {bus},
        'Distance (km)': {'$gte': 5}
    }

    data = list(conn['trip_summary'].find(query))


if __name__ == "__main__":
    main()
