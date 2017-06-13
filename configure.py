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


def configure(modelName):
    modelNames = ['BaseModel.json', 'RealisticModel.json']

    if modelName:
        modelNames.append(modelName)

    model = {}
    for modelName in modelNames:
        with open(modelName, 'r') as modelFile:
            modelChanges = json.load(modelFile)
            model.update(modelChanges)

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
    :param dataType: The type of data (MC or data)
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
