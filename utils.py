#! /usr/bin/env python


"""
Common code between various models
"""


def performance_by_year(model, year, tier):
    """
    Return various performance metrics based on the year under consideration
    (allows for step and continous variations)

    :param model: The model paremeters
    :param year: The year in which processing is done
    :param tier: Data tier produced

    :return:  tuple of cpu time and data size
    """

    cpuPerEvent = None
    sizePerEvent = None

    for modelYear in sorted(model['tier_sizes'][tier].keys()):
        if int(year) >= int(modelYear):
            sizePerEvent = model['tier_sizes'][tier][modelYear]

    return cpuPerEvent, sizePerEvent
