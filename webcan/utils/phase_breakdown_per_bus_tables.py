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
from pymongo import MongoClient
import pandas as pd
import tabulate
from itertools import chain
phase_types = {
    0: 'Idle',
    1: 'ACCEL FROM ZERO ',
    2: 'CRUISE',
    3: 'DECEL TO ZERO',
    4: 'INT ACCEL',
    5: 'INT DECEL'
}

pd.set_option('display.float_format', lambda x: '%.3f' % x)
def main():
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
        'adl_metro_2452',
    ]
    for bus in buses:
        query = {
            'vid': bus,
            'Distance (km)': {'$gte': 5}
        }

        data = conn['trip_summary'].find(query)
        rows = [x for x in chain(*([p for p in r['phases'] if p['Duration (s)'] > 4] for r in data))]
        phases = pd.DataFrame(rows)
        total_durations = phases['Duration (s)']
        total_duration = float(total_durations.sum())
        tbl = []
        for i in 0, 1, 2, 3, 4, 5:
            ps = phases[phases.phasetype == i]
            durations = ps['Duration (s)']
            tbl.append({
                'Phase Number': i,
                'Phase Type': phase_types[i].title(),
                'Total Duration': durations.sum(),
                'No. Phases': len(ps),
                'Mean Duration': durations.mean(),
                'Median Duration': durations.median(),
                'Proportion': durations.sum() / float(total_duration) * 100,
            })
        tbl.append({
            'Phase Number': '',
            'Phase Type': "Total",
            'Total Duration': total_duration,
            'No. Phases': len(phases),
            'Mean Duration': total_durations.mean(),
            'Median Duration': total_durations.median(),
            'Proportion': '100',
        })
        print(bus)
        print(tabulate.tabulate(tbl, headers='keys'))


if __name__ == "__main__":
    main()
