#! /usr/bin/env python

from __future__ import division

import sys
import collections
import matplotlib.pyplot as plt
import numpy as np
import json

# Basic parameters
kilo = 1000
mega = 1000 * kilo
giga = 1000 * mega
tera = 1000 * giga
peta = 1000 * tera
seconds_per_year = 86400 * 365

# Load base parameters
with open('BaseModel.json', 'r') as baseFile:
    model = json.load(baseFile)

# Load and apply model parameters
with open('RealisticModel.json') as modelFile:
    modelChanges = json.load(modelFile)

model.update(modelChanges)

mc_factor = model['mc_event_factor']
software_improvement_factor = float(sys.argv[1])
cpu_improvement_factor = float(sys.argv[2])
retirement_rate = 0.05

# The very important list of years
years = list(range(model['start_year'], model['end_year']+1))
# Annyoing kludge for later plotting
plotyears = [x-0.5 for x in years]
plotyears.append(model['end_year'] + 0.5)

software_improvement = {i : software_improvement_factor ** (i + 1 - model['start_year'])
                            for i in years}

# LHC processing times as of 2017; these need verification
data_reco_time_lhc = 250 #this is per HS
mc_gensim_time_lhc = 500 #this is per HS
mc_digi_time_lhc = 100 #this is per HS
mc_reco_time_lhc = data_reco_time_lhc

# HL-LHC processing times as of 2017
data_reco_time_hllhc = 4.00 * kilo #this is per HS
mc_gensim_time_hllhc = 1.50 * kilo #this is per HS
mc_digi_time_hllhc = 2.27 * kilo #this is per HS
mc_reco_time_hllhc = data_reco_time_hllhc

# Calculate the times by year assuming the software improvement factor...
# for simplicity we fill the arrays with the standard LHC values...
reco_time = {i : data_reco_time_lhc/software_improvement[i] for i in years}
sim_time = {i : (mc_gensim_time_lhc + mc_digi_time_lhc + mc_reco_time_lhc)
                /software_improvement[i] for i in years}

# ...but for 2026 and 2027, override this with the HL-LHC numbers!
# (sorry about the kludge)

for year in range(model['hl_start_year'], model['end_year']+1):
    reco_time[year] = data_reco_time_hllhc/software_improvement[year]
    sim_time[year] = (mc_gensim_time_hllhc + mc_digi_time_hllhc +
                      mc_reco_time_hllhc)/software_improvement[year]

# Running time: assume that running years (full years)
# are all the same number of seconds, shutdown years are zero
# 2026 is a little kludgy, it's a half year?

data_seconds = {i : 7.8E06 for i in years}
data_seconds[2019] = 0
data_seconds[2020] = 0
data_seconds[2024] = 0
data_seconds[2025] = 0

# For completeness, an array of trigger rates, which we assume to be 1 kHz
# until the HL-LHC starts in 2026.

trigger_rate = {i : 1.0 * kilo for i in years}
trigger_rate[2026] = 10.0 * kilo
trigger_rate[2027] = 10.0 * kilo

# CPU time requirement calculations

data_events = {i : data_seconds[i] * trigger_rate[i] for i in years}
mc_events = {i : data_events[i] * mc_factor for i in years}
data_cpu_time = {i : data_events[i] * reco_time[i] for i in years}
mc_cpu_time = {i : mc_events[i] * sim_time[i] for i in years}
total_cpu_time = {i : data_cpu_time[i] + mc_cpu_time[i] for i in years}

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
print cpu_capacity
for i in years:
    cpu_capacity[i] = cpu_capacity[i-1] * (1 - retirement_rate) + (300 if i < 2020 else 600) * kilo * cpu_improvement[i]
del cpu_capacity[2016]    

#cpu_capacity = {i : cpu_capacity[i-1] * (1 - retirement_rate) + 300 * kilo * cpu_improvement[i] for i in years}

# However, in 2026, switch to a computing model in which we devote twice as
# much of the budget to CPU, so there is a magic doubling.

#cpu_capacity[2026] *= 2
#cpu_capacity[2027] *= 2

for i in years: print i, '{:04.3f}'.format((data_cpu_time[i] +
    mc_cpu_time[i]) / tera), '{:04.3f}'.format(cpu_capacity[i] *
    seconds_per_year / tera), 'THS06', '{:04.3f}'.format((data_cpu_time[i] +
    mc_cpu_time[i])/(cpu_capacity[i] *
    seconds_per_year))

# Try to plot this

plt.hist(years, plotyears, 
             weights=[v*seconds_per_year/tera for v in cpu_capacity.values()],
             rwidth=0.8)
plt.plot(years, [v/tera for v in total_cpu_time.values()])
plt.ylabel('THS06s')
plt.xlabel('Year')
plt.title('CPU improvement ' + sys.argv[1] +
              ' Software improvement = ' + sys.argv[2])

    
plt.show()
