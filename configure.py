#! /usr/bin/env python
"""
Load the model parameters from two JSON files

 BaseModel.json - static things that are not going to change based on the assumptions of the model
 [modelName] - more dynamic parameters that will change based on conservative/optimistic assumptions
 Also load in the number of events expected per year from the detector

 Return all of this as a nested dictionary
"""

import json
from collections import namedtuple

from utils import time_dependent_value

SECONDS_PER_YEAR = 365.25 * 24 * 3600

def updateDict(target,changes):
    for k,v in changes.items():
        if k in target and isinstance(target[k],dict):
            updateDict(target[k],v)
        else:
            target[k]=v


def configure(modelName):
    modelNames = ['BaseModel.json', 'RealisticModel.json']

    if isinstance(modelName, basestring):
        modelNames.append(modelName)
    elif isinstance(modelName, list):
        modelNames.extend(modelName)

    model = {}
    for modelName in modelNames:
        with open(modelName, 'r') as modelFile:
            modelChanges = json.load(modelFile)
            updateDict(model,modelChanges)
#            model.update(modelChanges)

    return model


def in_shutdown(model, year):
    """
    :param model: The configuration dictionary
    :param year: check if this year is in a shutdown period
    :return: boolean for in shutdown, integer for last year not in shutdown
    """

    inShutdown = year in model['shutdown_years']

    while year in model['shutdown_years']:
        year -= 1

    return inShutdown, year


def run_model(model, year, data_type='data'):
    """
    :param model: The configuration dictionary
    :param year: The year the model is being queried for
    :param data_type: The type of data (MC or data)
    :return: data events, in_shutdown
    """

    RunModel = namedtuple('RunModel', 'events, in_shutdown')

    inShutdown, lastRunningYear = in_shutdown(model, year)
    events = 0
    if not inShutdown:
        triggerRate, basisYear = time_dependent_value(year, model['trigger_rate'])
        liveFraction, basisYear = time_dependent_value(year, model['live_fraction'])
        events = SECONDS_PER_YEAR * liveFraction * triggerRate
    if data_type == 'mc':
        events *= model['mc_event_factor']
    return RunModel(events, inShutdown)


def mc_event_model(model, year):
    """
    Given the various types of MC and their fraction compared to data in mc_evolution,
    for a the queried year, return the number of events needed to be simulated of each
    "MC year" in that calendar year.

    :param model: The configuration dictionary
    :param year: The year the model is being queried for
    :return: dictionary of {year1: events, year2: events} of types of events needed to be simualted
    """

    mcEvolution = model['mc_evolution']
    mcEvents = {}
    for mcType, ramp in mcEvolution.items():
        mcYear = int(mcType)

        # First figure out what to base the number of MC events
        currEvents = run_model(model, year).events
        if in_shutdown(model, year)[0]:
            lastYear = in_shutdown(model, year)[1]
            lastEvents = run_model(model, lastYear).events
        else:
            lastEvents = 0

        if mcYear > year:
            futureEvents = run_model(model, mcYear).events
        else:
            futureEvents = 0
        dataEvents = max(currEvents, lastEvents, futureEvents)

        # TODO: Replace this bit of code with interpolate_value from utils.py
        pastYear = 0
        futureYear = 3000
        mc_fraction = None
        for otherType in sorted(ramp):
            otherYear = int(otherType)
            if year == otherYear:  # We found the exact value
                mc_fraction = ramp[otherType]
                break
            if year - otherYear < year - pastYear and year > otherYear:
                pastYear = otherYear
            if otherYear > year:
                futureYear = otherYear
                break

        if mc_fraction is None:  # We didn't get an exact value, interpolate between two values
            mc_fraction = (ramp[str(pastYear)] + (year - pastYear) *
                           (ramp[str(futureYear)] - ramp[str(pastYear)]) / (futureYear - pastYear))

        mcEvents[mcType] = mc_fraction * dataEvents

    return mcEvents
