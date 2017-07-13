#! /usr/bin/env python


"""
Common code between various models
"""

from __future__ import absolute_import, division, print_function

from utils import interpolate_value


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

    # TODO:  Big old hack for now because we don't have "kind" for data
    if not kind:
        # print year
        kind = str(year)
    if kind not in ['2016', '2026']:
        if int(kind) >= 2025:
            kind = '2026'
        else:
            kind = '2017'
    kind = str(kind)

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
        improvement_factor = 1.0
        ramp = model['improvement_factors']['software_by_kind'][kind]
        for improve_year in range(int(model['start_year']), int(year) + 1):
            year_factor = interpolate_value(ramp, improve_year)
            improvement_factor *= year_factor

        cpuPerEvent = cpuPerEvent / improvement_factor
    except KeyError:  # CPU model does not know this tier
        cpuPerEvent = None

    return cpuPerEvent, sizePerEvent
