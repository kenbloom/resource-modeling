#! /usr/bin/env python

import json
import sys

fileName = sys.argv[1]

data = None

with open(fileName, 'r') as jsonFile:
    data = json.load(jsonFile)

with open(fileName, 'w') as jsonFile:
    json.dump(data, jsonFile, indent=1, sort_keys=True)

