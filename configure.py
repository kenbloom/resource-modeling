#! /usr/bin/env python

import json


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
