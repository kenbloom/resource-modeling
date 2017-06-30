#! /usr/bin/env python

"""
Usage: ./cpu.py config1.json,config2.json,...,configN.json

Determine the disk and tape models by running under various configuration changes. BaseModel.json and RealisticModel.json
provide defaults and configN.json overrides values in those configs or earlier ones in the list
"""

from __future__ import division, print_function

import sys

from configure import configure, mc_event_model, run_model
from plotting import plotEvents

GIGA = 1e9

modelNames = None
if len(sys.argv) > 1:
    modelNames = sys.argv[1].split(',')
model = configure(modelNames)

YEARS = list(range(model['start_year'], model['end_year'] + 1))

# Call the data model with a random year to get the fields
dataKinds = [key + ' MC' for key in mc_event_model(model, 2020).keys()]
dataKinds.append('Data')

eventsByYear = [[0 for _i in range(len(dataKinds))] for _j in YEARS]

for year in YEARS:
    eventsByYear[YEARS.index(year)][dataKinds.index('Data')] = run_model(model, year).events / GIGA
    mcEvents = mc_event_model(model, year)
    for mcKind, count in mcEvents.items():
        eventsByYear[YEARS.index(year)][dataKinds.index(mcKind + ' MC')] = count / GIGA

plotEvents(eventsByYear, name='Produced by Kind.png', title='Events produced by type', columns=dataKinds, index=YEARS)
