#! /usr/bin/env python


"""
Common plotting code
"""

from __future__ import absolute_import, division, print_function
from matplotlib import cm

import pandas as pd

# Make sort order that includes tiers from unrefined to refined and both string and integer years
SORT_ORDER = ['Run1 & 2015', 'Ops space', 'RAW', 'GENSIM', 'AOD', 'MINIAOD', 'NANOAOD', 'USER'] + \
             [str(year) for year in range(2006, 2050)] + list(range(2006, 2050))

cmap=cm.get_cmap('Paired')
colors=[ cmap(i) for i in range(0,10)]
COLOR_MAP = 'Paired'


def plotStorageWithCapacity(data, name, title='', columns=None, bars=None):
    bars = sorted(bars, key=SORT_ORDER.index)
    frame = pd.DataFrame(data, columns=columns)
    # ax = frame[['Capacity', 'Year']].plot(x='Year', linestyle='-', marker='o', color='Black')
    # ax = frame[bars + ['Year']].plot(x='Year', kind='bar', stacked=True, ax=ax, colormap=COLOR_MAP)
    ax = frame[bars + ['Year']].plot(x='Year', kind='bar', stacked=True, colormap=COLOR_MAP)
    ax.set(ylabel='PB', title=title)

    handles, labels = ax.get_legend_handles_labels()
    handles=handles[::-1]
    labels=labels[::-1]

    ax.legend(handles,labels,loc='best', markerscale=0.25, fontsize=11)
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    fig = ax.get_figure()
    fig.savefig(name)


def plotStorage(data, name, title='', columns=None, index=None):
    # Make the plot of produced data per year (input to other plots)
    plot_order = sorted(columns, key=SORT_ORDER.index)
    order_inds = [ SORT_ORDER.index(p) for p in plot_order]

    frame = pd.DataFrame(data, columns=columns, index=index)
#    ax = frame[plot_order].plot(kind='bar', stacked=True, colormap=COLOR_MAP)
    ax = frame[plot_order].plot(kind='bar', stacked=True, color=[colors[i] for i in order_inds])
    ax.set(ylabel='PB', title=title)

    handles, labels = ax.get_legend_handles_labels()
    handles=handles[::-1]
    labels=labels[::-1]

    ax.legend(handles,labels,loc='best', markerscale=0.25, fontsize=11)
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    fig = ax.get_figure()
    fig.tight_layout()

    fig.savefig(name)


def plotEvents(data, name, title='', columns=None, index=None):
    # Make the plot of produced events per year by type (input to other plots)
    plot_order = sorted(columns)
    order_inds = [ SORT_ORDER.index(p) for p in plot_order]
    frame = pd.DataFrame(data, columns=columns, index=index)
    ax = frame[plot_order].plot(kind='bar', stacked=True, colormap=COLOR_MAP)
    ax.set(ylabel='Billions of events', title=title)
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
    fig = ax.get_figure()
    fig.savefig(name)
