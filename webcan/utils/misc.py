import numpy as np


def calc_extra(i, previous):
    """
    Given an instantaneous reading, return the extra fields
    :param i:
    :param previous:
    :return:
    """
    if previous is None or (i['timestamp'] - previous['timestamp']).total_seconds() > 3:
        return {}
    else:
        air_fuel_ratio = 14.7
        density_ulp = 0.755
        # co2_per_litre = 2234.628
        petrol_cents_per_litre = 130

        elec_kg_co2_per_kwh = 0.53
        e_cents_per_kwh = 41.8

        # emissions values taken from: http://www.environment.gov.au/system/files/resources/e30b1895-4870-4a1f-9b32-3a590de3dddf/files/national-greenhouse-accounts-factors-august-2016.pdf
        # density_diesel = 0.766
        # air_diesel_ratio = 16.1
        # co2_per_litre_diesel = 2700
        diesel_cents_per_litre = 136.5

        gj_per_kl_of_euro_iv = 38.6
        gj_per_kl_of_gas = 34.2
        gj_to_kwh = 277.778

        co2_per_gj_petrol = 67.4
        ch4_per_gj_petrol = 0.5
        n2o_per_gj_petrol = 1.8

        co2_per_gj_diesel = 69.9
        ch4_per_gj_diesel = 0.06
        n2o_per_gj_diesel = 0.5

        time_diff = (i['timestamp'] - previous['timestamp']).total_seconds()

        out = {}

        out['_duration'] = time_diff
        if i.get('PID_MAF_FLOW (grams/sec)'):
            fuel_use = (i['PID_MAF_FLOW (grams/sec)'] * time_diff) / density_ulp / air_fuel_ratio
            out['Petrol Used (ml)'] = fuel_use
            # out['Petrol CO2e (g)'] = fuel_use * (co2_per_litre / 1000)
            gj_used = fuel_use / 1000000 * gj_per_kl_of_gas
            out['Petrol CO2e (g)'] = (np.array(
                [co2_per_gj_petrol, ch4_per_gj_petrol, n2o_per_gj_petrol]) * gj_used).sum() * 1000
            out['Petrol cost (c)'] = fuel_use / 1000 * petrol_cents_per_litre
            out['P Used (kWh)'] = gj_used * gj_to_kwh
        if i.get('FMS_FUEL_ECONOMY (L/h)'):
            fuel_use = i['FMS_FUEL_ECONOMY (L/h)'] * time_diff / 3600  # use in L
            out['Petrol Used (ml)'] = fuel_use * 1000
            gj_used = fuel_use / 1000000 * gj_per_kl_of_euro_iv
            out['Petrol CO2e (g)'] = (np.array(
                [co2_per_gj_diesel, ch4_per_gj_diesel, n2o_per_gj_diesel]) * gj_used).sum() * 1000
            out['Petrol cost (c)'] = fuel_use * diesel_cents_per_litre
            out['P Used (kWh)'] = gj_used * gj_to_kwh
        if i.get('Battery Voltage (V)'):
            i['Power (kW)'] = i['Battery Voltage (V)'] * i['Charge Current (A)'] / 1000
            energy_use = i['Power (kW)'] * time_diff / -3600  # kWh
            out['E Used (kWh)'] = energy_use
            out['E CO2e (g)'] = energy_use * elec_kg_co2_per_kwh / 1000
            out['E cost (c)'] = energy_use * e_cents_per_kwh
        if i.get('BUSTECH_BATTERY (Voltage V)'):
            i['Power (kW)'] = i['BUSTECH_BATTERY (Voltage V)'] * i['BUSTECH_BATTERY (Current A)'] / 1000
            energy_use = i['Power (kW)'] * time_diff / 3600
            out['E Used (kWh)'] = energy_use
            out['E CO2e (g)'] = energy_use * elec_kg_co2_per_kwh / 1000
            out['E cost (c)'] = energy_use * e_cents_per_kwh
        out['Total CO2e (g)'] = out.get('E CO2e (g)', 0) + out.get('Petrol CO2e (g)', 0)
        out['Total Energy (kWh)'] = out.get('E Used (kWh)', 0) + out.get('P Used (kWh)', 0)
        return out
