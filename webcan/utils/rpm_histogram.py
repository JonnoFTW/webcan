import configparser
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

    for bus in buses:
        trips = [s['trip_key'] for s in conn['trip_summary'].find({'vid': bus, 'Distance (km)': {'$gte': 5}},
                                                                  {'trip_key': 1})]
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
                    "boundaries": [
                        1.0,
                        100.0,
                        200.0,
                        300.0,
                        400.0,
                        500.0,
                        600.0,
                        700.0,
                        800.0,
                        900.0,
                        1000.0,
                        1100.0,
                        1200.0,
                        1300.0,
                        1400.0,
                        1500.0,
                        1600.0,
                        1700.0,
                        1800.0,
                        1900.0,
                        2000.0,
                        2100.0,
                        2200.0,
                        2300.0,
                        2400.0,
                        2500.0,
                        2600.0,
                        2700.0,
                        2800.0,
                        2900.0,
                        3000.0,
                        3100.0,
                        3200.0,
                        3300.0,
                        3400.0,
                        3500.0,
                        3600.0,
                        3700.0,
                        3800.0,
                        3900.0,
                        4000.0,
                        4100.0,
                        4200.0,
                        4300.0,
                        4400.0,
                        4500.0,
                        4600.0,
                        4700.0,
                        4800.0,
                        4900.0,
                        5000.0
                    ],
                    "default": "Error"
                }
            }
        ], allowDiskUse=True
        )
        print(list(readings))


if __name__ == "__main__":
    plot()
