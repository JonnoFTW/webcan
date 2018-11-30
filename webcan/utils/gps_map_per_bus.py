import configparser
from pymongo import MongoClient
import csv
from tqdm import tqdm

def readings_to_csv():
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
        trips = [s['trip_key'] for s in conn['trip_summary'].find({'vid': bus, 'Distance (km)': {'$gte': 5}},
                                                                  {'trip_key': 1})]
        print("Fetching", bus)
        readings = conn['rpi_readings'].find({'trip_key': {'$in': trips}},
                                             {'pos': 1, 'vid': 1, 'trip_key': 1, '_id': 0})
        i = 0
        prog = tqdm(total=readings.count())
        with open('/scratch/fms/{}.csv'.format(bus), 'w') as outfile:
            writer = csv.DictWriter(outfile, ['lat', 'lng', 'trip_key', 'vid'])
            writer.writeheader()
            for r in readings:
                i += 1
                if i % 16 == 0:
                    writer.writerow({
                        'lat': r['pos']['coordinates'][1],
                        'lng': r['pos']['coordinates'][0],
                        'trip_key': r['trip_key'],
                        'vid': r['vid']
                    })
                prog.update()

if __name__ == "__main__":
    readings_to_csv()
