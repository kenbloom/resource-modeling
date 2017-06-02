#! /usr/bin/env python

from __future__ import division, print_function

import json
from collections import defaultdict

import pandas as pd

from configure import configure

PETA = 1e15

model = configure('RealisticModel.json')
YEARS = list(range(model['start_year'], model['end_year'] + 1))
TIERS = list(model['tier_size'])

# Disk space used
dataProduced = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataProduced[year][type][tier]
dataOnDisk = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataOnDisk[year][type][tier]
dataOnTape = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dataOnTape[year][type][tier]
diskSamples = defaultdict(list)
tapeSamples = defaultdict(list)

diskCopies = {}
tapeCopies = {}
for tier in TIERS:
    diskCopies[tier] = [versions * replicas for versions, replicas in
                        zip(model['storage_model']['versions'][tier], model['storage_model']['disk_replicas'][tier])]
    tapeCopies[tier] = model['storage_model']['versions'][tier][0] * model['storage_model']['tape_replicas'][tier]

# Loop over years to determine how much is produced without versions or replicas
for year in YEARS:
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
for year in YEARS:
    for producedYear, dataDict in dataProduced.items():
        for dataType, tierDict in dataDict.items():
            for tier, size in tierDict.items():
                diskCopiesByDelta = diskCopies[tier]
                tapeCopiesByDelta = tapeCopies[tier]
                if int(producedYear) <= int(year):  # Can't save data for future years
                    if year - producedYear >= len(diskCopiesByDelta):
                        diskSize = size * diskCopiesByDelta[-1]  # Use the data for the last year
                        tapeSize = size * tapeCopiesByDelta[-1]  # Use the data for the last year
                    else:
                        diskSize = size * diskCopiesByDelta[year - producedYear]
                        tapeSize = size * tapeCopiesByDelta[year - producedYear]
                    if diskSize:
                        dataOnDisk[year][dataType][tier] += diskSize
                        diskSamples[year].append([producedYear, dataType, tier, diskSize])
                    if tapeSize:
                        dataOnTape[year][dataType][tier] += tapeSize
                        tapeSamples[year].append([producedYear, dataType, tier, tapeSize])

# Initialize a matrix with tiers and years
diskByTierYear = [[0 for _i in range(len(TIERS))] for _j in YEARS]
tapeByTierYear = [[0 for _i in range(len(TIERS))] for _j in YEARS]

for year, dataDict in dataOnDisk.items():
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            diskByTierYear[YEARS.index(year)][TIERS.index(tier)] += size / PETA

for year, dataDict in dataOnTape.items():
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            tapeByTierYear[YEARS.index(year)][TIERS.index(tier)] += size / PETA

diskFrame = pd.DataFrame(diskByTierYear, columns=TIERS, index=YEARS)
ax = diskFrame.plot(kind='bar', stacked=True)
ax.set(ylabel='PB on disk')
fig = ax.get_figure()
fig.savefig('Disk by Tier.png')

tapeFrame = pd.DataFrame(tapeByTierYear, columns=TIERS, index=YEARS)
ax = tapeFrame.plot(kind='bar', stacked=True)
ax.set(ylabel='PB on tape')
fig = ax.get_figure()
fig.savefig('Tape by Tier.png')

with open('disk_samples.json', 'w') as diskUsage, open('tape_samples.json', 'w') as tapeUsage:
    json.dump(diskSamples, diskUsage, sort_keys=True, indent=1)
    json.dump(tapeSamples, tapeUsage, sort_keys=True, indent=1)


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
