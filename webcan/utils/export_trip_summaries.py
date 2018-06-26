import configparser
import csv
import pymongo

if __name__ == "__main__":
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']
    conn = pymongo.MongoClient(uri)
    trip_summary = conn['webcan']['trip_summary']
    summaries = list(trip_summary.find({}, {'_id': 0, 'phases': 0}))
    with open('trip_summary.csv', 'w') as fout:
        writer = csv.DictWriter(fout, fieldnames=summaries[0].keys())
        writer.writeheader()
        writer.writerows(summaries)
