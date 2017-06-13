#! /usr/bin/env python

from __future__ import division
from __future__ import print_function

import sys
import collections
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
from configure import configure, run_model
from utils import performance_by_year

# Basic parameters
kilo = 1000
mega = 1000 * kilo
giga = 1000 * mega
tera = 1000 * giga
peta = 1000 * tera
seconds_per_year = 86400 * 365
seconds_per_month = 86400 * 30
running_time = 7.8E06

model = configure('RealisticModel.json')

mc_factor = model['mc_event_factor']
software_improvement_factor = model['improvement_factors']['software']
cpu_improvement_factor = model['improvement_factors']['hardware']
retirement_rate = 0.05

# The very important list of years
YEARS = list(range(model['start_year'], model['end_year']+1))

# Get the performance year by year which includes the software improvement factor
reco_time = {year: performance_by_year(model, year, 'RECO', data_type='data')[0] for year in YEARS}
sim_time = {year: performance_by_year(model, year, 'GENSIM', data_type='mc')[0] +
                  performance_by_year(model, year, 'DIGI',data_type='mc')[0] +
                  performance_by_year(model, year, 'RECO', data_type='mc')[0] for year in YEARS}

# CPU time requirement calculations, in HS06 * s
# Take the running time and event rate from the model

data_events = {i: run_model(model, i, data_type='data').events for i in YEARS}
mc_events = {i: run_model(model, i, data_type='mc').events for i in YEARS}

data_cpu_time = {i : data_events[i] * reco_time[i] for i in YEARS}
mc_cpu_time = {i : mc_events[i] * sim_time[i] for i in YEARS}

# The data need to be reconstructed about as quickly as we record them.  In
# addition, we need to factor in express, repacking, AlCa, CAF
# functionality and skimming.  Presumably these all scale like the data.
# Per the latest CRSG document, these total to 123 kHS06 compared to 240
# kHS016 for the prompt reconstruction, which we can round to 50%, so
# multiply by 50%.  (Ignoring the 10 kHS06 needed for VO boxes, which
# won't scale up and is also pretty small.)  In-year reprocessing model:
# assume we will re-reco 10% of the data each year, but we want to
# complete it in one month.


data_cpu_required = {i : (1.5 * data_cpu_time[i] / running_time
                              + 0.1 * data_cpu_time[i] / seconds_per_month)
                         for i in YEARS}

# The corresponding MC, on the other hand, can be reconstructed over an
# entire year.  We can use this to calculate the HS06 needed to do those
# tasks.

mc_cpu_required = {i : mc_cpu_time[i] / seconds_per_year for i in YEARS}


total_cpu_required = {i : data_cpu_required[i] + mc_cpu_required[i] for i in YEARS}



# Then, CPU availability calculations.  This follows the "Available CPU
# power" spreadsheet.  Take a baseline value of 1.4 MHS06 in 2016, in
# future years subtract 5% of the previous for retirements, and add 300
# kHS06 which gets improved by the cpu_improvement in each year, until
# 2020, during LS2, when we shift the computing model to start buying an
# improved 600 kHS06 per year.

# This is kludgey -- need to establish the baseline to make the
# caluculation work, but once the calculation is there, delete the baseline
# for the histogram to work.  Not to mention that I couldn't get the
# dictionary comprehension to work here.

cpu_improvement = {i : cpu_improvement_factor ** (i-2017) for i in YEARS}

cpu_capacity = {2016 : 1.4 * mega}

for i in YEARS:
    cpu_capacity[i] = cpu_capacity[i-1] * (1 - retirement_rate) + (300 if i < 2020 else 600) * kilo * cpu_improvement[i]
del cpu_capacity[2016]    

# CPU capacity model ala disk.py

# Set the initial points
cpuCapacity = {str(model['capacity_model']['cpu_year']): model['capacity_model']['cpu_start']}

# A bit of a kludge. Assume what we have now was bought and will be retired in equal chunks over its lifetime
cpuAdded = {}
for year in range(model['capacity_model']['cpu_year'] - model['capacity_model']['cpu_lifetime'] + 1,
                  model['capacity_model']['cpu_year'] + 1):
    retired = model['capacity_model']['cpu_start'] / model['capacity_model']['cpu_lifetime']
    cpuAdded[str(year)] = retired

cpuFactor = model['improvement_factors']['hardware']

for year in YEARS:
    if str(year) not in cpuCapacity:
        cpuDelta = 0  # Find the delta which can be time dependant
        cpuDeltas = model['capacity_model']['cpu_delta']
        for deltaYear in sorted(cpuDeltas.keys()):
            if int(year) >= int(deltaYear):
                lastCpuYear = int(deltaYear)
                cpuDelta = model['capacity_model']['cpu_delta'][deltaYear]
                
        cpuAdded[str(year)] = cpuDelta * cpuFactor ** (int(year) - int(lastCpuYear))

        # Retire cpu added N years ago or retire 0

        cpuRetired = cpuAdded.get(str(int(year) - model['capacity_model']['cpu_lifetime']), 0)
        cpuCapacity[str(year)] = cpuCapacity[str(int(year) - 1)] + cpuAdded[str(year)] - cpuRetired


for i in YEARS:
    print(i, '{:04.3f}'.format(data_cpu_required[i] / mega),
    '{:04.3f}'.format(mc_cpu_required[i] / mega),
    '{:04.3f}'.format(cpu_capacity[i] / mega), 
    '{:04.3f}'.format(cpuCapacity[str(i)] / mega), 'MHS06',
    '{:04.3f}'.format((data_cpu_required[i] + mc_cpu_required[i])/
                          (cpu_capacity[i])))

# Try to plot this

# Squirt the dictionary entries into lists:

cpuDataList = []
for year, item in sorted(data_cpu_required.items()):
    cpuDataList.append(item/mega)
cpuMCList = []
for year, item in sorted(mc_cpu_required.items()):
    cpuMCList.append(item/mega)
cpuCapacityList = []
for year, item in sorted(cpu_capacity.items()):
    cpuCapacityList.append(item/mega)
altCapacityList = []
for year, item in sorted(cpuCapacity.items()):
    altCapacityList.append(item/mega)
    
# Build a data frame from lists:

cpuFrame = pd.DataFrame({'Year': [str(year) for year in YEARS],
                             'Data' : cpuDataList,
                             'MC' : cpuMCList,
                             'Capacity' : cpuCapacityList,
                             'AltCapacity' : altCapacityList}
                            )


ax = cpuFrame[['Year','Capacity']].plot(x='Year',linestyle='-',marker='o', color='Red')
cpuFrame[['Year','AltCapacity']].plot(x='Year',linestyle='-',marker='o', color='Blue',ax=ax)
cpuFrame[['Year', 'Data', 'MC']].plot(x='Year',kind='bar',stacked=True,ax=ax)
ax.set(ylabel='MHS06')
ax.set(title='CPU improvement %s Software improvement = %s' %
           (cpu_improvement_factor, software_improvement_factor))

fig = ax.get_figure()
fig.savefig('CPU by Type.png')

