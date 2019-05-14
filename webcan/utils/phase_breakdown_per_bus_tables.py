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
from itertools import chain

phase_types = {
    0: 'Idle',
    1: 'ACCEL FROM ZERO ',
    2: 'CRUISE',
    3: 'DECEL TO ZERO',
    4: 'INT ACCEL',
    5: 'INT DECEL'
}


def main():
    import pandas as pd
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
    pd.options.display.float_format = '{:.2f}'.format
    tbl = []
    for bus in buses:
        query = {
            'vid': bus,
            'Distance (km)': {'$gte': 5}
        }

        data = conn['trip_summary'].find(query)
        rows = [x for x in chain(*([p for p in r['phases'] if p['Duration (s)'] > 4] for r in data))]
        phases = pd.DataFrame(rows)
        total_durations = phases['Duration (s)']
        total_duration = total_durations.sum()

        for i in 0, 1, 2, 3, 4, 5:
            ps = phases[phases.phasetype == i]
            durations = ps['Duration (s)']
            mag_mean = 0
            mag_median = 0
            mag_std = 0
            suffix = ""
            if i == 1:
                coef = ps['Coeff Beta (km/h)/√(Δt)']
                # plt.figure()
                # coef.hist(bins=range(0,30),label=bus)
                # plt.legend()
                # plt.show()
                mag_mean = coef.mean()
                mag_median = coef.median()
                mag_std = coef.std()
                suffix = "(km/h)/√(Δt)"
            elif i == 2:
                mean_speed = ps['Mean Speed (km/h)']
                mag_mean = mean_speed.mean()
                mag_median = mean_speed.median()
                mag_std = mean_speed.std()
                suffix = "km/h"
            elif i >= 2:
                delta_speed = (ps['Finish Speed (km/h)'] - ps['Start Speed (km/h)']) / ps['Duration (s)']
                mag_mean = delta_speed.mean()
                mag_median = delta_speed.median()
                mag_std = delta_speed.std()
                suffix = "km/h/s"

            tbl.append({
                'Vehicle': bus.split('_')[0],
                'Phase Number': i,
                'Phase Type': phase_types[i].title(),
                'Total Duration': durations.sum(),
                'No. Phases': len(ps),
                'Mean Duration': "{:.2f}".format(durations.mean()),
                'Median Duration': "{:.2f}".format(durations.median()),
                'Duration Proportion': "{:.2f}".format(durations.sum() / float(total_duration) * 100),
                'Average Magnitude': "{:.2f} {}".format(mag_mean, suffix),
                'Median Magnitude':  "{:.2f} {}".format(mag_median, suffix),
                'Std Dev Magnitude': "{:.2f} {}".format(mag_std, suffix)
            })
        tbl.append({
            'Vehicle': bus,
            'Phase Number': '',
            'Phase Type': "Total",
            'Total Duration': total_duration,
            'No. Phases': len(phases),
            'Mean Duration': "{:.2f}".format(total_durations.mean()),
            'Median Duration': "{:.2f}".format(total_durations.median()),
            'Duration Proportion': '100',
        })
        print(bus)
    import csv
    with open('./out/phase_breakdowns.csv', 'w') as fout:
        writer = csv.DictWriter(fout, tbl[0].keys())
        writer.writeheader()
        writer.writerows(tbl)
            
        # print(tabulate.tabulate(tbl, headers='keys', tablefmt='csv'))


if __name__ == "__main__":
    main()
