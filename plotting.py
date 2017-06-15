#! /usr/bin/env python


"""
Common plotting code
"""

from __future__ import absolute_import, division, print_function

import pandas as pd

# Make sort order that includes tiers from unrefined to refined and both string and integer years
SORT_ORDER = ['Run1 & 2', 'Ops space', 'RAW', 'GENSIM', 'AOD', 'MINIAOD', 'MICROAOD', 'USER'] + \
             [str(year) for year in range(2006, 2050)] + list(range(2006, 2050))
COLOR_MAP = 'Paired'


def plotStorageWithCapacity(data, name, title='', columns=None, bars=None):
    bars = sorted(bars, key=SORT_ORDER.index)
    frame = pd.DataFrame(data, columns=columns)
    ax = frame[['Capacity', 'Year']].plot(x='Year', linestyle='-', marker='o', color='Black')
    frame[bars + ['Year']].plot(x='Year', kind='bar', stacked=True, ax=ax, colormap=COLOR_MAP)
    ax.set(ylabel='PB', title=title)
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    fig = ax.get_figure()
    fig.savefig(name)


def plotStorage(data, name, title='', columns=None, index=None):
    columns = sorted(columns, key=SORT_ORDER.index)
    # Make the plot of produced data per year (input to other plots)
    frame = pd.DataFrame(data, columns=columns, index=index)
    ax = frame.plot(kind='bar', stacked=True, colormap=COLOR_MAP)
    ax.set(ylabel='PB', title=title)
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    fig = ax.get_figure()
    fig.savefig(name)
