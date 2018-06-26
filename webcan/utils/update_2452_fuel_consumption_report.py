import configparser
import tqdm
from pymongo import MongoClient, ASCENDING, DESCENDING
import numpy as np

from webcan.utils.misc import gj_per_kl_of_euro_iv, co2_per_gj_diesel, ch4_per_gj_diesel, n2o_per_gj_diesel, gj_to_kwh


def main():
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    conn = MongoClient(uri)['webcan']

    """
    get all trip reports for 2452, and calculate their:
     total fuel consumption
     mean fuel rate
     total co2e
    """
    trip_keys = list(conn.trip_summary.distinct('trip_key', {'vid': 'adl_metro_2452'}))
    for trip_key in tqdm.tqdm(trip_keys, desc='Trip Reports: ', unit=' trips'):
        fr = conn.rpi_readings.find_one({
            'trip_key': trip_key,
            'FMS_FUEL_CONSUMPTION (L)': {'$exists': True}
        }, sort=[('trip_sequence', ASCENDING)])

        lr = conn.rpi_readings.find_one({
            'trip_key': trip_key,
            'FMS_FUEL_CONSUMPTION (L)': {'$exists': True}
        }, sort=[('trip_sequence', DESCENDING)])

        total_fuel_used_litres = lr['FMS_FUEL_CONSUMPTION (L)'] - fr['FMS_FUEL_CONSUMPTION (L)']
        duration_seconds = (lr['timestamp'] - fr['timestamp']).total_seconds()
        duration_hours = duration_seconds / 3600.0
        # print(f"FUEL Used (L) {total_fuel_used_litres} Duration (s) {duration_seconds}")

        fuel_use_ml = total_fuel_used_litres * 1000.
        gj_used = fuel_use_ml / 1000000 * gj_per_kl_of_euro_iv
        total_co2e = (np.array(
            [co2_per_gj_diesel, ch4_per_gj_diesel, n2o_per_gj_diesel]) * gj_used).sum() * 1000

        total_energy = gj_used * gj_to_kwh

        conn.trip_summary.update_one(
            {'trip_key': trip_key},
            {'$set': {
                'Total Fuel (ml)': fuel_use_ml,
                'Mean Fuel Rate (L/h)': total_fuel_used_litres / duration_hours,
                'Total CO2e (g)': total_co2e,
                'Total Energy (kWh)': total_energy
            }}
        )


if __name__ == "__main__":
    main()
