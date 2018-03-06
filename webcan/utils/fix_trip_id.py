import pymongo
import pytz


def main():
    utc = pytz.utc
    adl_tz = pytz.timezone('Australia/Adelaide')
    uri = 'mongodb://mack0242:McK1Tfraf1C@traffic-db01r.it.ad.flinders.edu.au:27017/mack0242'

    client = pymongo.MongoClient(uri)
    readings = client.mack0242.rpi_readings

    for trip in readings.distinct('trip_id'):
        rows = readings.find({'trip_id': trip}).sort([('timestamp', pymongo.ASCENDING)])
        try:
            first = next(obj for obj in rows if obj['timestamp'] is not None)
        except StopIteration as e:
            print(trip, "has no timestamps, removing")
            readings.remove({'trip_id': trip})
            continue
        # get the earliest timestamp and use that
        old_trip_id = first['trip_id']
        dt = first['timestamp']
        pieces = old_trip_id.split('_')
        ts = utc.localize(dt).astimezone(adl_tz).strftime("%Y%m%d_%H%M%S")
        if len(pieces) == 2:
            trip_id = "{}_{}".format(ts, first['vid'])
        else:
            trip_id = "{}_{}".format(ts, '_'.join(pieces[2:]))
        new_trip_id = trip_id.replace(' ', '_')
        print("Old:", old_trip_id, "\t\t\tNew:", new_trip_id)
        readings.update_many({
            'trip': trip
        }, {
            '$set': {'trip': new_trip_id},
        })


if __name__ == "__main__":
    main()
