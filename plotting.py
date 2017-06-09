#! /usr/bin/env python


"""
Common plotting code
"""

from __future__ import absolute_import, division, print_function

import pandas as pd


def plotStorageWithCapacity(data, name, title='', columns=None, bars=None):
    frame = pd.DataFrame(data, columns=columns)
    ax = frame[bars + ['Year']].plot(x='Year', kind='bar', stacked=True)
    frame[['Capacity', 'Year']].plot(x='Year', linestyle='-', marker='o', color='Black', ax=ax)
    ax.set(ylabel='PB', title=title)
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    fig = ax.get_figure()
    fig.savefig(name)


def plotStorage(data, name, title='', columns=None, index=None):

    # Make the plot of produced data per year (input to other plots)
    frame = pd.DataFrame(data, columns=columns, index=index)
    ax = frame.plot(kind='bar', stacked=True)
    ax.set(ylabel='PB', title=title)
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    fig = ax.get_figure()
    fig.savefig(name)

