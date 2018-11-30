from .generate_xy_plot import plot

duration = 'Duration (s)'
co2 = 'Total CO2 (g)'
beta_coeff = 'Coeff Beta (km/h)/√(Δt)'


def diff(p):
    return p['Finish Speed (km/h)'] - p['Start Speed (km/h)']


def f1(p):
    if p['phasetype'] == 1 and p[duration] > 4 and p[co2] > 0:
        return p[beta_coeff], p[co2] / p[duration]


def f2(p):
    if p['phasetype'] == 2 and p[duration] > 4 and p[co2] > 0:
        return p['Mean Speed (km/h)'], p[co2] / p[duration]


def f3(p):
    d = diff(p)
    if p['phasetype'] == 3 and p[duration] > 4 and p[co2] > 0 and d < 0:
        return d / p[duration], p[co2] / p[duration]


def f4(p):
    d = diff(p)
    if p['phasetype'] == 4 and p[duration] > 4 and p[co2] > 0 and d > 0:
        return d / p[duration], p[co2] / p[duration]


def f5(p):
    d = diff(p)
    if p['phasetype'] == 5 and p[duration] > 4 and p[co2] > 0 and d < 0:
        return d / p[duration], p[co2] / p[duration]


if __name__ == "__main__":
    plot(f1,
         beta_coeff,
         'CO2 per Second',
         'Acceleration from Zero Profile for ',
         'Comparison of Acceleration from Zero Model Trendlines',
         (0, 30),
         (0, 55)
         )
    plot(f3,
         'Deceleration Rate (km/h/s)',
         'CO2 Per Second (g/s)',
         'Deceleration to Zero Profile for ',
         'Comparison of Deceleration to Idle Model Trendlines',
         (-10, 0),
         (0, 55),
         )
    plot(f4,
         'Acceleration Rate (km/h/s)',
         'CO2 Per Second (g/s)',
         'Intermediate Acceleration Profile for ',
         'Comparison of Intermediate Acceleration Model Trendlines',
         (0, 10),
         (0, 55),
         )
    plot(f5,
         'Deceleration Rate (km/h/s)',
         'CO2 Per Second (g/s)',
         'Intermediate Deceleration Profile for ',
         'Comparison of Intermediate Deceleration Model Trendlines',
         (-10, 0),
         (0, 55),
         )
    plot(f2,
         'Mean Cruise Speed',
         'CO2 Per Second (g/s)',
         'Cruise Emissions for ',
         'Comparison of Cruise Emissions Model Trendlines',
         (0, 110),
         (0, 55))
