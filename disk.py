#! /usr/bin/env python

from __future__ import division, print_function

import json
import sys
from collections import defaultdict

import pandas as pd

from configure import configure, in_shutdown
from utils import performance_by_year

PETA = 1e15

modelName = None
if len(sys.argv) > 1:
    modelName = sys.argv[1]

model = configure(modelName)
YEARS = list(range(model['start_year'], model['end_year'] + 1))
TIERS = list(model['tier_sizes'].keys())

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
    # Assume we have the highest number of versions in year 1, save n replicas of that
    tapeCopies[tier] = model['storage_model']['versions'][tier][0] * model['storage_model']['tape_replicas'][tier]

# Loop over years to determine how much is produced without versions or replicas
for year in YEARS:
    for tier in TIERS:
        dummyCPU, tierSize = performance_by_year(model, year, tier)
        if tier not in model['mc_only_tiers']:
            dataProduced[year]['data'][tier] += tierSize * model['eventCounts']['data'][str(year)]
        if tier not in model['data_only_tiers']:
            dataProduced[year]['mc'][tier] += tierSize * model['eventCounts']['mc'][str(year)]

print("Data Produced by year and tier")
for year, dataDict in dataProduced.items():
    print(" %s" % year)
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            print("  %10s (%4s): %10.3f PB" % (tier, dataType, size / PETA))

# Initialize a matrix with years and years
diskByYear = [[0 for _i in YEARS] for _j in YEARS]
tapeByYear = [[0 for _i in YEARS] for _j in YEARS]

# Loop over years to determine how much is saved
for year in YEARS:
    for producedYear, dataDict in dataProduced.items():
        for dataType, tierDict in dataDict.items():
            for tier, size in tierDict.items():
                diskCopiesByDelta = diskCopies[tier]
                tapeCopiesByDelta = tapeCopies[tier]
                if int(producedYear) <= int(year):  # Can't save data for future years
                    if year - producedYear >= len(diskCopiesByDelta):
                        revOnDisk = diskCopiesByDelta[-1]  # Revisions = versions * copies
                        revOnTape = tapeCopiesByDelta[-1]  # Assume what we have for the last year is good for out years
                    elif in_shutdown(model, year):
                        inShutdown, lastRunningYear = in_shutdown(model, year)
                        revOnDisk = diskCopiesByDelta[lastRunningYear - producedYear]
                        revOnTape = tapeCopiesByDelta[lastRunningYear - producedYear]
                    else:
                        revOnDisk = diskCopiesByDelta[year - producedYear]
                        revOnTape = tapeCopiesByDelta[year - producedYear]
                    if size and revOnDisk:
                        dataOnDisk[year][dataType][tier] += size * revOnDisk
                        diskSamples[year].append([producedYear, dataType, tier, size * revOnDisk, revOnDisk])
                        diskByYear[YEARS.index(year)][YEARS.index(producedYear)] += size  * revOnDisk/ PETA
                    if size and revOnTape:
                        dataOnTape[year][dataType][tier] += size * revOnTape
                        tapeSamples[year].append([producedYear, dataType, tier, size * revOnTape, revOnTape])
                        tapeByYear[YEARS.index(year)][YEARS.index(producedYear)] += size * revOnTape/ PETA

# Initialize a matrix with tiers and years
diskByTier = [[0 for _i in range(len(TIERS))] for _j in YEARS]
tapeByTier = [[0 for _i in range(len(TIERS))] for _j in YEARS]

for year, dataDict in dataOnDisk.items():
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            diskByTier[YEARS.index(year)][TIERS.index(tier)] += size / PETA

for year, dataDict in dataOnTape.items():
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            tapeByTier[YEARS.index(year)][TIERS.index(tier)] += size / PETA

diskFrame = pd.DataFrame(diskByTier, columns=TIERS, index=YEARS)
ax = diskFrame.plot(kind='bar', stacked=True)
ax.set(ylabel='PB on disk')
fig = ax.get_figure()
fig.savefig('Disk by Tier.png')

tapeFrame = pd.DataFrame(tapeByTier, columns=TIERS, index=YEARS)
ax = tapeFrame.plot(kind='bar', stacked=True)
ax.set(ylabel='PB on tape')
fig = ax.get_figure()
fig.savefig('Tape by Tier.png')

diskByYearFrame = pd.DataFrame(diskByYear, columns=YEARS, index=YEARS)
ax = diskByYearFrame.plot(kind='bar', stacked=True)
ax.set(ylabel='PB on disk')
fig = ax.get_figure()
fig.savefig('Disk by Year.png')

tapeByYearFrame = pd.DataFrame(tapeByYear, columns=YEARS, index=YEARS)
ax = tapeByYearFrame.plot(kind='bar', stacked=True)
ax.set(ylabel='PB on tape')
fig = ax.get_figure()
fig.savefig('Tape by Year.png')

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
