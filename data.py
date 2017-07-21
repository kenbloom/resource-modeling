#! /usr/bin/env python

"""
Usage: ./cpu.py config1.json,config2.json,...,configN.json

Determine the disk and tape models by running under various configuration changes. BaseModel.json and RealisticModel.json
provide defaults and configN.json overrides values in those configs or earlier ones in the list
"""

from __future__ import division, print_function

import json
import sys
from collections import defaultdict

from configure import configure, in_shutdown, mc_event_model, run_model
from plotting import plotStorage, plotStorageWithCapacity
from utils import time_dependent_value
from performance import performance_by_year

PETA = 1e15

modelNames = None
if len(sys.argv) > 1:
    modelNames = sys.argv[1].split(',')
model = configure(modelNames)

YEARS = list(range(model['start_year'], model['end_year'] + 1))
TIERS = list(model['tier_sizes'].keys())
STATIC_TIERS = list(sorted(set(model['static_disk'].keys() + model['static_tape'].keys())))

# Build the capacity model

# Set the initial points
diskCapacity = {str(model['capacity_model']['disk_year']): model['capacity_model']['disk_start']}
tapeCapacity = {str(model['capacity_model']['tape_year']): model['capacity_model']['tape_start']}

# A bit of a kludge. Assume what we have now was bought and will be retired in equal chunks over its lifetime
diskAdded = {}
tapeAdded = {}
for year in range(model['capacity_model']['disk_year'] - model['capacity_model']['disk_lifetime'] + 1,
                  model['capacity_model']['disk_year'] + 1):
    retired = model['capacity_model']['disk_start'] / model['capacity_model']['disk_lifetime']
    diskAdded[str(year)] = retired
for year in range(model['capacity_model']['tape_year'] - model['capacity_model']['tape_lifetime'] + 1,
                  model['capacity_model']['tape_year'] + 1):
    retired = model['capacity_model']['tape_start'] / model['capacity_model']['tape_lifetime']
    tapeAdded[str(year)] = retired

diskFactor = model['improvement_factors']['disk']
tapeFactor = model['improvement_factors']['tape']

for year in YEARS:
    if str(year) not in diskCapacity:
        diskDelta = 0  # Find the delta which can be time dependant
        tapeDelta = 0  # Find the delta which can be time dependant
        diskDeltas = model['capacity_model']['disk_delta']
        tapeDeltas = model['capacity_model']['tape_delta']
        for deltaYear in sorted(diskDeltas.keys()):
            if int(year) >= int(deltaYear):
                lastDiskYear = int(deltaYear)
                diskDelta = model['capacity_model']['disk_delta'][deltaYear]
        for deltaYear in sorted(tapeDeltas.keys()):
            if int(year) >= int(deltaYear):
                lastTapeYear = int(deltaYear)
                tapeDelta = model['capacity_model']['tape_delta'][deltaYear]

        diskAdded[str(year)] = diskDelta * diskFactor**(int(year) - int(lastDiskYear))
        tapeAdded[str(year)] = tapeDelta * tapeFactor**(int(year) - int(lastTapeYear))
        # Retire disk/tape added N years ago or retire 0

        diskRetired = diskAdded.get(str(int(year) - model['capacity_model']['disk_lifetime']), 0)
        tapeRetired = tapeAdded.get(str(int(year) - model['capacity_model']['tape_lifetime']), 0)
        diskCapacity[str(year)] = diskCapacity[str(int(year) - 1)] + diskAdded[str(year)] - diskRetired
        tapeCapacity[str(year)] = tapeCapacity[str(int(year) - 1)] + tapeAdded[str(year)] - tapeRetired

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
    if not tapeCopies[tier]: tapeCopies[tier] = [0, 0, 0]

# Loop over years to determine how much is produced without versions or replicas
for year in YEARS:
    for tier in TIERS:
        if tier not in model['mc_only_tiers']:
            dummyCPU, tierSize = performance_by_year(model, year, tier, data_type='data')
            dataProduced[year]['data'][tier] += tierSize * run_model(model, year, data_type='data').events
        if tier not in model['data_only_tiers']:
            mcEvents = mc_event_model(model, year)
            for kind, events in mcEvents.items():
                dummyCPU, tierSize = performance_by_year(model, year, tier, data_type='mc', kind=kind)
                dataProduced[year]['mc'][tier] += tierSize * events

producedByTier = [[0 for _i in range(len(TIERS))] for _j in YEARS]
for year, dataDict in dataProduced.items():
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            producedByTier[YEARS.index(year)][TIERS.index(tier)] += size / PETA

# Initialize a matrix with tiers and years
YearColumns = YEARS + ['Capacity', 'Year', 'Run1 & 2']  # Add capacity, years as columns for data frame

# Initialize a matrix with years and years
diskByYear = [[0 for _i in YearColumns] for _j in YEARS]
tapeByYear = [[0 for _i in YearColumns] for _j in YEARS]

# Loop over years to determine how much is saved
for year in YEARS:
    # Add static (or nearly) data
    for tier, spaces in model['static_disk'].items():
        size, producedYear = time_dependent_value(year=year, values=spaces)
        dataOnDisk[year]['Other'][tier] += size
        diskSamples[year].append([producedYear, 'Other', tier, size])
        diskByYear[YEARS.index(year)][YEARS.index(producedYear)] += size / PETA
    for tier, spaces in model['static_tape'].items():
        size, producedYear = time_dependent_value(year=year, values=spaces)
        dataOnTape[year]['Other'][tier] += size
        tapeSamples[year].append([producedYear, 'Other', tier, size])
        tapeByYear[YEARS.index(year)][YEARS.index(producedYear)] += size / PETA

    # Figure out data from this year and previous
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
                        diskByYear[YEARS.index(year)][YEARS.index(producedYear)] += size * revOnDisk / PETA
                    if size and revOnTape:
                        dataOnTape[year][dataType][tier] += size * revOnTape
                        tapeSamples[year].append([producedYear, dataType, tier, size * revOnTape, revOnTape])
                        tapeByYear[YEARS.index(year)][YEARS.index(producedYear)] += size * revOnTape / PETA

    # Add capacity numbers
    diskByYear[YEARS.index(year)][YearColumns.index('Capacity')] = diskCapacity[str(year)] / PETA
    diskByYear[YEARS.index(year)][YearColumns.index('Year')] = str(year)
    tapeByYear[YEARS.index(year)][YearColumns.index('Capacity')] = tapeCapacity[str(year)] / PETA
    tapeByYear[YEARS.index(year)][YearColumns.index('Year')] = str(year)

# Initialize a matrix with tiers and years
# Add capacity, years, and fake tiers as columns for the data frame
TierColumns = TIERS + ['Capacity', 'Year'] + STATIC_TIERS

diskByTier = [[0 for _i in range(len(TierColumns))] for _j in YEARS]
tapeByTier = [[0 for _i in range(len(TierColumns))] for _j in YEARS]
for year, dataDict in dataOnDisk.items():
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            diskByTier[YEARS.index(year)][TierColumns.index(tier)] += size / PETA
    diskByTier[YEARS.index(year)][TierColumns.index('Capacity')] = diskCapacity[str(year)] / PETA
    diskByTier[YEARS.index(year)][TierColumns.index('Year')] = str(year)
for year, dataDict in dataOnTape.items():
    for dataType, tierDict in dataDict.items():
        for tier, size in tierDict.items():
            tapeByTier[YEARS.index(year)][TierColumns.index(tier)] += size / PETA
    tapeByTier[YEARS.index(year)][TierColumns.index('Capacity')] = tapeCapacity[str(year)] / PETA
    tapeByTier[YEARS.index(year)][TierColumns.index('Year')] = str(year)

diskByTier[YEARS.index(2017)][TierColumns.index('Run1 & 2')] = 25
diskByTier[YEARS.index(2018)][TierColumns.index('Run1 & 2')] = 10
diskByTier[YEARS.index(2019)][TierColumns.index('Run1 & 2')] = 5
diskByTier[YEARS.index(2020)][TierColumns.index('Run1 & 2')] = 0

diskByYear[YEARS.index(2017)][YearColumns.index('Run1 & 2')] = 25
diskByYear[YEARS.index(2018)][YearColumns.index('Run1 & 2')] = 10
diskByYear[YEARS.index(2019)][YearColumns.index('Run1 & 2')] = 5
diskByYear[YEARS.index(2020)][YearColumns.index('Run1 & 2')] = 0

plotStorage(producedByTier, name='Produced by Tier.png', title='Data produced by tier', columns=TIERS, index=YEARS)

plotStorageWithCapacity(tapeByTier, name='Tape by Tier.png', title='Data on tape by tier', columns=TierColumns,
                        bars=TIERS + STATIC_TIERS)
plotStorageWithCapacity(diskByTier, name='Disk by Tier.png', title='Data on disk by tier', columns=TierColumns,
                        bars=TIERS + STATIC_TIERS)
plotStorageWithCapacity(tapeByYear, name='Tape by Year.png', title='Data on tape by year produced', columns=YearColumns,
                        bars=YEARS + ['Run1 & 2'])
plotStorageWithCapacity(diskByYear, name='Disk by Year.png', title='Data on disk by year produced', columns=YearColumns,
                        bars=YEARS + ['Run1 & 2'])

# Dump out tuples of all the data on tape and disk in a given year
with open('disk_samples.json', 'w') as diskUsage, open('tape_samples.json', 'w') as tapeUsage:
    json.dump(diskSamples, diskUsage, sort_keys=True, indent=1)
    json.dump(tapeSamples, tapeUsage, sort_keys=True, indent=1)


# disk printout
print('\nDisk by tier printout in PB\n')
header = "year"
for column in TIERS + STATIC_TIERS:
    header += ";"
    header += str(column)
header +=";total;40%"
print(header)

for year in YEARS:
    line = str(year)
    total = 0
    for column in TIERS + STATIC_TIERS:
        line += " " 
        line += '{:8.2f}'.format(diskByTier[YEARS.index(year)][TierColumns.index(column)])
        total += diskByTier[YEARS.index(year)][TierColumns.index(column)]
    line += '{:8.2f}'.format(total)
    line += '{:8.2f}'.format(total*0.4)
    print(line)


# tape printout
print('\nTape by tier printout in PB\n')
header = "year"
for column in TIERS + STATIC_TIERS:
    header += ";"
    header += str(column)
header +=";total;40%"
print(header)

for year in YEARS:
    line = str(year)
    total = 0
    for column in TIERS + STATIC_TIERS:
        line += " " 
        line += '{:8.2f}'.format(tapeByTier[YEARS.index(year)][TierColumns.index(column)])
        total += tapeByTier[YEARS.index(year)][TierColumns.index(column)]
    line += '{:8.2f}'.format(total)
    line += '{:8.2f}'.format(total*0.4)
    print(line)

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
