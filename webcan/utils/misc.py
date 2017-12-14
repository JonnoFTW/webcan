def calc_extra(i, previous):
    """
    Given an instantaneous reading, return the extra fields
    :param i:
    :param previous:
    :return:
    """
    if previous is None:
        return {}
    else:
        air_fuel_ratio = 14.7
        density_ulp = 0.755
        co2_per_litre = 2234.628
        petrol_cents_per_litre = 130
        elec_kg_co2_per_kwh = 0.53
        e_cents_per_kwh = 41.8
        time_diff = (i['timestamp'] - previous['timestamp']).total_seconds()
        out = {}
        if i.get('PID_MAF_FLOW (grams/sec)'):
            fuel_use = (i['PID_MAF_FLOW (grams/sec)'] * time_diff) / density_ulp / air_fuel_ratio
            out['Petrol Used (ml)'] = fuel_use
            out['Petrol CO2 (g)'] = fuel_use * (co2_per_litre / 1000)
            out['Petrol cost (c)'] = fuel_use / 1000 * petrol_cents_per_litre
        if i.get('Power (kW)'):
            energy_use = max(0, i['Power (kW)'] * time_diff / 3600 / 10 * -1)
            out['E Used (kWh)'] = energy_use
            out['E CO2 (g)'] = energy_use * elec_kg_co2_per_kwh / 1000
            out['E cost (c)'] = energy_use * e_cents_per_kwh
        out['Total CO2 (g)'] = out.get('E CO2 (g)', 0) + out.get('Petrol CO2 (g)', 0)
        return out
