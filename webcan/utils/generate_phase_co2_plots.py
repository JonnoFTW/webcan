import configparser

from collections import defaultdict
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
    vid_re = '^adl_metro_1905'

    query = {
        # 'vid': vid_re,
        'vid': {'$regex': vid_re},
        'Distance (km)': {'$gte': 10}
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
        series = defaultdict(lambda: dict(x=[], y=[]))
        for summary in data[:2]:
            summary_of_phase = [s for s in summary['phases'] if
                                s['phasetype'] == params['phasetype'] and s[params['y']] != 0]
            for f in 'xy':
                series[summary['vid']][f].extend(pluck(summary_of_phase, params[f]))
        for vid, xy in series.items():
            x, y = xy['x'], xy['y']
            plt.scatter(x, y, label=vid)
        plt.legend()
        plt.xlabel(params['x'])
        plt.ylabel(params['y'])
        xmin = min(x for x in series.values())
        ymin = min(x for x in series.values())
        plt.title("{} vs {} phase={} n={}".format(
            params['x'],
            params['y'],
            params['phasetype'],
            sum(len(y) for y in series.values())
        ))
        plt.show()


if __name__ == "__main__":
    main()
