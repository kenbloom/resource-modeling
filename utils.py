#! /usr/bin/env python


"""
Common code between various models
"""

from __future__ import absolute_import, division, print_function


def performance_by_year(model, year, tier, data_type=None, kind=None):
    """
    Return various performance metrics based on the year under consideration
    (allows for step and continuous variations)

    :param model: The model parameters
    :param year: The year in which processing is done
    :param tier: Data tier produced
    :param data_type: data or mc
    :param kind: The year flavor of MC or data. May differ from actual running year

    :return:  tuple of cpu time (HS06 * s) and data size
    """

    # If we don't specify flavors, assume we are talking about the current year
    if not kind:
        kind = year

    try:
        for modelYear in sorted(model['tier_sizes'][tier].keys()):
            if int(kind) >= int(modelYear):
                sizePerEvent = model['tier_sizes'][tier][modelYear]
    except KeyError:  # Storage model does not know this tier
        sizePerEvent = None

    try:
        # Look up the normalized processing time
        for modelYear in sorted(model['cpu_time'][data_type][tier].keys()):
            if int(kind) >= int(modelYear):
                cpuPerEvent = model['cpu_time'][data_type][tier][modelYear]

        # Apply the year by year correction
        cpuPerEvent = cpuPerEvent / (model['improvement_factors']['software']) ** (1 + year - model['start_year'])
    except KeyError:  # CPU model does not know this tier
        cpuPerEvent = None

    return cpuPerEvent, sizePerEvent


def time_dependent_value(year=2016, values=None):
    """
    :param year: Year for which we are looking for parameter
    :param values: dictionary in the form {"2016": 1.0, "2017": 2.0}
    :return: determined value, first year for which its valid (for calculating improvements from a known point)

    """

    values = values or {}
    value = None
    lastYear = None
    for deltaYear in sorted(values.keys()):
        if int(year) >= int(deltaYear):
            lastYear = int(deltaYear)
            value = values[deltaYear]

    return value, lastYear
