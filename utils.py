#! /usr/bin/env python


"""
Common code between various models
"""

from __future__ import absolute_import, division, print_function


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


def interpolate_value(ramp, year):
    """
    Takes a dictionary of the form
    {"2016": x,
     "2020": y,
     ...
     }

     and returns x for year=2016, y for year=2020, and an interpolated value for 2017, 2018, 2019
    """

    pastYear = 0
    futureYear = 3000
    value = None
    for otherType in sorted(ramp):
        otherYear = int(otherType)
        if year == otherYear:  # We found the exact value
            value = ramp[otherType]
            break
        if year - otherYear < year - pastYear and year > otherYear:
            pastYear = otherYear
        if otherYear > year:
            futureYear = otherYear
            break

    if value is None:  # We didn't get an exact value, interpolate between two values
        value = (ramp[str(pastYear)] + (year - pastYear) *
                 (ramp[str(futureYear)] - ramp[str(pastYear)]) / (futureYear - pastYear))

    return value

###

# from configure import configure
#
# model = configure(None)
#
# performance_by_year(model, 2023, 'RECO', data_type='mc', kind='2017')
