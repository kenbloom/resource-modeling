#! /usr/bin/env python

import json

"""
Load the model parameters from two JSON files
 
 BaseModel.json - static things that are not going to change based on the assumptions of the model
 [modelName] - more dynamic parameters that will change based on conservative/optimistic assumptions
 Also load in the number of events expected per year from the detector
 
 Return all of this as a nested dictionary 
"""


def configure(modelName):
    # Load base parameters
    with open('BaseModel.json', 'r') as baseFile:
        model = json.load(baseFile)

    # Load and apply model parameters
    with open(modelName) as modelFile:
        modelChanges = json.load(modelFile)

    model.update(modelChanges)

    try:
        with open('EventCounts.json', 'r') as eventFile:
            model['eventCounts'] = json.load(eventFile)
    except IOError:
        model['eventCounts'] = {}

    return model
