import configparser

__author__ = 'mack0242'

import csv
import pymongo
from pyproj import Proj, transform
import datetime
import glob


def trim_leading(x):
    try:
        if len(x) > 1:
            return int(x.lstrip("0"))
        return int(x)
    except:
        return -1


def parse_float(x):
    try:
        return float(x)
    except:
        return float(-1)


converters = {
    'Date': lambda x: datetime.datetime.strptime(x, "%d/%m/%Y").date(),
    'Time': lambda x: datetime.datetime.strptime(x, "%I:%M %p").time(),
    'Involves_4WD': lambda x: x.lower() == 'y',
    'Area_Speed': trim_leading,
    'RRD': parse_float,
    'Total_Damage': trim_leading,
    'Total_Vehicles_Involved': trim_leading
}


def do_import():
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    mongo_uri = conf['app:webcan']['mongo_uri']
    with pymongo.MongoClient(mongo_uri) as client:
        db = client['mack0242']
        crashes = db['crashes']
        p1 = Proj(init='epsg:3107')
        p2 = Proj(init='epsg:4326')
        r = 0
        for path in glob.glob('/scratch/crashes/*_DATA_SA_Crash.csv'):
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['ACCLOC_X']:
                        try:
                            x, y = transform(p1, p2, float(row['ACCLOC_X']), float(row['ACCLOC_Y']))
                        except:
                            print(row)
                            exit(1)
                        row['loc'] = {'type': 'Point', 'coordinates': [x, y]}
                        for i, j in converters.items():
                            i = i.replace(' ', '_')
                            row[i] = j(row[i])
                        row['datetime'] = datetime.datetime.combine(row['Date'], row['Time'])
                        del row['ACCLOC_X']
                        del row['ACCLOC_Y']
                        del row['Date']
                        del row['Time']
                        del row['Year']
                        del row['DayName']
                        try:

                            # crashes.insert(row)
                            r += 1
                        except Exception as e:
                            print(e)
                            print(row)
                            exit(1)

        print("Rows inserted:", r)


if __name__ == "__main__":
    import time

    start = time.clock()
    do_import()
    print("Took: ", time.clock() - start, "s")
