#! /usr/bin/env python

from __future__ import division, print_function

from collections import defaultdict

from configure import configure

model = configure('RealisticModel.json')

# Disk space used
dataProduced = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataProduced[year][type][tier]
dataOnDisk = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataOnDisk[year][type][tier]
dataOnTape = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataOnTape[year][type][tier]

# Loop over years to determine how much is produced
for year in list(range(model['start_year'], model['end_year']+1)):
    for tier, tierSize in model['tier_size'].items():
        dataProduced[year]['data'][tier] += tierSize * model['eventCounts']['data'][str(year)]
        dataProduced[year]['mc'][tier] += tierSize * model['eventCounts']['mc'][str(year)]

print("Data Produced by year and tier")
for year, dataDict in dataProduced.items():
    print(" %s" % year)
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            print("  %10s (%4s): %10.3f PB" % (tier, dataType, size/1e15))

# Loop over years to determine how much is saved
for year in list(range(model['start_year'], model['end_year']+1)):
    for producedYear, dataDict in dataProduced.items():
        for dataType, tierDict in dataDict.items():
            for tier, size in tierDict.items():
                if int(producedYear) <= int(year):  # Just do a silly sum for now
                    dataOnDisk[year][dataType][tier] += size

print("Data on disk by year and tier")
for year, dataDict in dataOnDisk.items():
    print(" %s" % year)
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            print("  %10s (%4s): %10.3f PB" % (tier, dataType, size/1e15))
