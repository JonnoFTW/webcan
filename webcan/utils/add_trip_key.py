import configparser
from pymongo import MongoClient
from tqdm import tqdm

def main():
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    conn = MongoClient(uri, w=0)['mack0242']
    readings = conn['rpi_readings']
    cursor = readings.find()
    prog = tqdm(total=cursor.count())
    for doc in cursor:
        try:
            readings.update_one({'_id': doc['_id']},
                                {'$set': {'trip_key': doc['trip_id'].split('_')[2]}})
            prog.update()
        except IndexError as e:
            pass
    prog.close()


if __name__ == "__main__":
    main()
