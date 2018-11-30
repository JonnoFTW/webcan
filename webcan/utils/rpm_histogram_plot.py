import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import json
from glob import glob

if __name__ == "__main__":
    for fname in glob('./out/*.json'):
        print(fname)
        with open(fname) as f:
            counts = {int(k): v for k, v in json.load(f).items() if int(k) <= 2000}
            fig, ax = plt.subplots(figsize=(9, 5))
            loc = plticker.MultipleLocator(base=100)
            ax.xaxis.set_major_locator(loc)
            title = "RPM Histogram for " + fname.split('_')[-2]
            plt.title(title)
            plt.xlabel("RPM")
            plt.ylabel("Count")
            bins = []
            weights = []
            for k, c in sorted(counts.items()):
                bins.append(k)
                weights.append(c)
            plt.bar(bins, weights, width=25)
            plt.xlim(0, 2000)
            plt.legend()
            ax.grid()
            fig.savefig('./out/' + title + '.png')
    plt.show()
