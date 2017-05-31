#! /usr/bin/env python

from __future__ import division, print_function

from collections import defaultdict

from configure import configure

PETA = 1e15

model = configure('RealisticModel.json')

# Disk space used
dataProduced = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataProduced[year][type][tier]
dataOnDisk = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataOnDisk[year][type][tier]
dataOnTape = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataOnTape[year][type][tier]

# diskCopies = defaultdict(lambda: defaultdict(float))
diskCopies = {}
tapeCopies = {}
for tier in model['storage_model']['versions'].keys():
    diskCopies[tier] = [versions * replicas for versions, replicas in
                        zip(model['storage_model']['versions'][tier], model['storage_model']['disk_replicas'][tier])]
    tapeCopies[tier] = model['storage_model']['versions'][tier][0] * model['storage_model']['tape_replicas'][tier]

# Loop over years to determine how much is produced without versions or replicas
for year in list(range(model['start_year'], model['end_year'] + 1)):
    for tier, tierSize in model['tier_size'].items():
        dataProduced[year]['data'][tier] += tierSize * model['eventCounts']['data'][str(year)]
        dataProduced[year]['mc'][tier] += tierSize * model['eventCounts']['mc'][str(year)]

print("Data Produced by year and tier")
for year, dataDict in dataProduced.items():
    print(" %s" % year)
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            print("  %10s (%4s): %10.3f PB" % (tier, dataType, size / PETA))

# Loop over years to determine how much is saved
for year in list(range(model['start_year'], model['end_year'] + 1)):
    for producedYear, dataDict in dataProduced.items():
        for dataType, tierDict in dataDict.items():
            for tier, size in tierDict.items():
                copiesByDelta = diskCopies[tier]
                tapeCopiesByDelta = tapeCopies[tier]
                if int(producedYear) <= int(year):  # Can't save data for future years
                    if year - producedYear >= len(copiesByDelta):
                        dataOnDisk[year][dataType][tier] += size * copiesByDelta[-1]  # Use the data for the last year
                        dataOnTape[year][dataType][tier] += size * tapeCopiesByDelta[-1]  # Use the data for the last year
                    else:
                        dataOnDisk[year][dataType][tier] += size * copiesByDelta[year - producedYear]
                        dataOnTape[year][dataType][tier] += size * tapeCopiesByDelta[year - producedYear]

print("Data on disk by year and tier")
for year, dataDict in dataOnDisk.items():
    yearTotal = 0
    print(" %s" % year)
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            yearTotal += size
            print("  %10s (%4s): %10.3f PB" % (tier, dataType, size / PETA))
    print ("              Total: %10.3f PB" % (yearTotal / PETA))

print("Data on tape by year and tier")
for year, dataDict in dataOnTape.items():
    yearTotal = 0
    print(" %s" % year)
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            yearTotal += size
            print("  %10s (%4s): %10.3f PB" % (tier, dataType, size / PETA))
    print ("              Total: %10.3f PB" % (yearTotal / PETA))

'''
AOD:
current year: 1 version, fraction on disk, complete on tape
next year: 1 version, nothing on disk, complete on tape
next-to-next year: 0 versions

MINIAOD:
current year: 2 versions, one on disk, one on tape
next year: 1 version, fraction on disk, one version on tape
next-to-next year: 0 version

MICROAOD:
current year: 10 different versions (combination of multiple different MICROAODs and different versions), several replicas on disk, one on tape
next year: only the distinct set of different MICROAOD, no different version, several replicas on disk (less than current year), on distinct set on tape
next-to-next year: same as next year, but only one disk replica
next year:
'''
