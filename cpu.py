#! /usr/bin/env python

from __future__ import division
from __future__ import print_function

import sys
import collections
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
from configure import configure
from utils import performance_by_year

# Basic parameters
kilo = 1000
mega = 1000 * kilo
giga = 1000 * mega
tera = 1000 * giga
peta = 1000 * tera
seconds_per_year = 86400 * 365
running_time = 7.8E06

model = configure('RealisticModel.json')

mc_factor = model['mc_event_factor']
software_improvement_factor = model['improvement_factors']['software']
cpu_improvement_factor = model['improvement_factors']['hardware']
retirement_rate = 0.05

# The very important list of years
years = list(range(model['start_year'], model['end_year']+1))

# Get the performance year by year which includes the software improvement factor
reco_time = {year: performance_by_year(model, year, 'RECO', data_type='data')[0] for year in years}
sim_time = {year: performance_by_year(model, year, 'GENSIM', data_type='mc')[0] +
                  performance_by_year(model, year, 'DIGI',data_type='mc')[0] +
                  performance_by_year(model, year, 'RECO', data_type='mc')[0] for year in years}

# Running time: assume that running years (full years)
# are all the same number of seconds, shutdown years are zero
# 2026 is a little kludgy, it's a half year?

data_seconds = {i : running_time for i in years}
data_seconds[2019] = 0
data_seconds[2020] = 0
data_seconds[2024] = 0
data_seconds[2025] = 0

# For completeness, an array of trigger rates, which we assume to be 1 kHz
# until the HL-LHC starts in 2026.

trigger_rate = {i : 1.0 * kilo for i in years}
trigger_rate[2026] = 10.0 * kilo
trigger_rate[2027] = 10.0 * kilo

# CPU time requirement calculations, in HS06 * s

data_events = {i : data_seconds[i] * trigger_rate[i] for i in years}
mc_events = {i : data_events[i] * mc_factor for i in years}

data_cpu_time = {i : data_events[i] * reco_time[i] for i in years}
mc_cpu_time = {i : mc_events[i] * sim_time[i] for i in years}

# The data need to be reconstructed about as quickly as we record them.
# The corresponding MC, on the other hand, can be reconstructed over an
# entire year.  We can use this to calculate the HS06 needed to do those
# tasks.

data_cpu_required = {i : data_cpu_time[i] / running_time for i in years}
mc_cpu_required = {i : mc_cpu_time[i] / seconds_per_year for i in years}


total_cpu_required = {i : data_cpu_required[i] + mc_cpu_required[i] for i in years}



# Write out the number of events per year for use in other models
eventCounts = {}
with open('EventCounts.json', 'w') as eventFile:
    eventCounts['data'] = data_events
    eventCounts['mc'] = mc_events
    json.dump(eventCounts, eventFile, indent=1, sort_keys=True)

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

cpu_improvement = {i : cpu_improvement_factor ** (i-2017) for i in years}

cpu_capacity = {2016 : 1.4 * mega}

for i in years:
    cpu_capacity[i] = cpu_capacity[i-1] * (1 - retirement_rate) + (300 if i < 2020 else 600) * kilo * cpu_improvement[i]
del cpu_capacity[2016]    

#cpu_capacity = {i : cpu_capacity[i-1] * (1 - retirement_rate) + 300 * kilo * cpu_improvement[i] for i in years}

# However, in 2026, switch to a computing model in which we devote twice as
# much of the budget to CPU, so there is a magic doubling.

#cpu_capacity[2026] *= 2
#cpu_capacity[2027] *= 2

#for i in years: print i, '{:04.3f}'.format((data_cpu_required[i] +
#    mc_cpu_required[i]) / mega), '{:04.3f}'.format(cpu_capacity[i] / mega), 'MHS06', '{:04.3f}'.format((data_cpu_required[i] + mc_cpu_required[i])/(cpu_capacity[i]))

for i in years:
    print(i, '{:04.3f}'.format(data_cpu_required[i] / mega),
    '{:04.3f}'.format(mc_cpu_required[i] / mega),
    '{:04.3f}'.format(cpu_capacity[i] / mega), 'MHS06',
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

# Build a data frame from lists:

cpuFrame = pd.DataFrame({'Year': [str(year) for year in years],
                             'Data' : cpuDataList,
                             'MC' : cpuMCList,
                             'Capacity' : cpuCapacityList})


ax = cpuFrame[['Year','Capacity']].plot(x='Year',linestyle='-',marker='o', color='Red')
cpuFrame[['Year', 'Data', 'MC']].plot(x='Year',kind='bar',stacked=True,ax=ax)
ax.set(ylabel='MHS06')
ax.set(title='CPU improvement %s Software improvement = %s' %
           (cpu_improvement_factor, software_improvement_factor))

fig = ax.get_figure()
fig.savefig('CPU by Type.png')

