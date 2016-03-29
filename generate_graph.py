#!/usr/bin/env python

import os
import math
import numpy as np

from genshi.template import TemplateLoader
from genshi.core import Markup

color = ['#ff0056', '#0067db', '#008031', '#ff8607', '#c039ff']


class SVGPlot(object):
    def __init__(self,
                 width=58, height=82,
                 axis_width=46, axis_height=46,
                 axis_left=8.4, axis_top=3,
                 font='Myriad Pro', font_size=10,
                 xmin=None, xmax=None, x_tick_res=None, x_tick_integer=False, xlog=False,
                 ymin=None, ymax=None, y_tick_res=None, y_tick_integer=False, ylog=False,
                 data=[], xlabel='', ylabel='', markers=False,
                 inkscape_length_fix=True):

        self.width = width
        self.height = height
        self.axis_width = axis_width
        self.axis_height = axis_height
        self.axis_left = axis_left
        self.axis_top = axis_top
        self.font = font
        self.font_size = font_size

        if xmin is None:
            xmin = float(min([min(series[0]) for series in data]))

        if xmax is None:
            xmax = float(max([max(series[0]) for series in data]))

        if ymin is None:
            ymin = float(min([min(series[1]) for series in data]))

        if ymax is None:
            ymax = float(max([max(series[1]) for series in data]))

        if x_tick_res is None:
            x_tick_res = (xmax - xmin) / 5.0

        if y_tick_res is None:
            y_tick_res = (ymax - ymin) / 5.0

        self.xmin = float(xmin)
        self.xmax = float(xmax)
        self.xlog = xlog

        self.ymin = float(ymin)
        self.ymax = float(ymax)
        self.ylog = ylog

        self.x_tick_integer = x_tick_integer
        self.y_tick_integer = y_tick_integer
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.x_tick_res = float(x_tick_res)
        self.y_tick_res = float(y_tick_res)
        self.markers = markers
        self.data = data
        self.inkscape_length_fix = inkscape_length_fix

    def transform_axis(self, x, axis_min, axis_max, axis_start, axis_length, logarithmic):
        if logarithmic:
            x = np.log10(x)
            axis_min = np.log10(axis_min)
            axis_max = np.log10(axis_max)

        scale = axis_length / (axis_max - axis_min)
        offset = axis_start - axis_min*scale

        return x*scale + offset

    def transform_x(self, x):
        return self.transform_axis(x, self.xmin, self.xmax, self.axis_left, self.axis_width, self.xlog)

    def transform_y(self, y):
            return self.transform_axis(y, self.ymin, self.ymax,
                                       self.axis_top + self.axis_height, -self.axis_height, self.ylog)

    def tick_values(self, axis_min, axis_max, tick_resolution, logarithmic):
        if logarithmic:
            # The first task is to scale the tick resolution to a reference decade.
            # We pick 1--10 because it's convenient for the calculations.
            tick_resolution /= 10.0**np.floor(np.log10(tick_resolution))

            # We proceed one tick at a time.
            current_decade = np.floor(np.log10(axis_min))
            current_tick_resolution = tick_resolution * 10.0**current_decade
            start_tick = math.ceil(axis_min / current_tick_resolution) * current_tick_resolution

            ticks = [start_tick]

            new_tick = start_tick
            while ticks[-1] < axis_max:
                current_decade = np.floor(np.log10(new_tick + 0.1*current_tick_resolution))
                current_tick_resolution = 10.0**current_decade * tick_resolution
                new_tick += current_tick_resolution

                ticks.append(new_tick)

            return ticks

        else:
            start_tick = math.ceil(axis_min / tick_resolution) * tick_resolution
            return np.arange(start_tick, axis_max + tick_resolution/10, tick_resolution)

    def construct(self):

        pixels_per_millimeter = 3.7795
        if self.inkscape_length_fix:
            pixels_per_millimeter *= 90.0 / 96

        axis_origin = (self.axis_left, self.axis_top + self.axis_height)

        # M 15 57 L 30 52 L 67 5
        series_list = []
        for i, series in enumerate(self.data):
            x = np.array(series[0])
            y = np.array(series[1])

            x_transformed = self.transform_x(x) * pixels_per_millimeter
            y_transformed = self.transform_y(y) * pixels_per_millimeter

            if not np.isfinite(x_transformed).all() and np.isfinite(y_transformed).all():
                continue

            coordinates = ['%f %f' % p for p in zip(x_transformed, y_transformed)]

            markers = []
            if self.markers:
                markers = zip(x_transformed, y_transformed)

            series_list.append(('M ' + ' L'.join(coordinates), color[i % len(color)], markers))

        xticks = []
        yticks = []

        start_tick = math.ceil(self.xmin / self.x_tick_res) * self.x_tick_res

        for tick in self.tick_values(self.xmin, self.xmax, self.x_tick_res, self.xlog): #np.arange(start_tick, self.xmax + 1e-9, self.x_tick_res):
            position = self.transform_x(tick)

            if self.xmin < tick < self.xmax:
                style = 'display'
            else:
                style = 'hide'

            if self.x_tick_integer:
                tick = int(round(tick))

            xticks.append({'position': position,
                           'label': tick,
                           'style': style})

        start_tick = math.ceil(self.ymin / self.y_tick_res) * self.y_tick_res

        for tick in self.tick_values(self.ymin, self.ymax, self.y_tick_res, self.ylog): #np.arange(start_tick, self.ymax + 1e-9, self.y_tick_res):
            position = self.transform_y(tick)

            if self.ymin < tick < self.ymax:
                style = 'display'
            else:
                style = 'hide'

            if self.y_tick_integer:
                tick = int(round(tick))

            yticks.append({'position': position,
                           'label': tick,
                           'style': style})

        options = {
            'svg_width': self.width,
            'svg_height': self.height,
            'axis_width': self.axis_width,
            'axis_height': self.axis_height,
            'axis_left': self.axis_left,
            'axis_top': self.axis_top,
            'font': self.font,
            'font_size': self.font_size,
            'xticks': xticks,
            'yticks': yticks,
            'series': series_list,
            'xlabel': self.xlabel,
            'ylabel': self.ylabel,
            'data': self.data
        }

        loader = TemplateLoader(
            os.path.join(os.path.dirname(__file__), 'templates'),
            auto_reload=True
        )
        template = loader.load('template.svg')
        return template.generate(**options).render('xml')


if __name__ == '__main__':
    x = np.linspace(-2, 2, 10)
    y = x ** 2

    plot = SVGPlot(data=[(x, y)], xlabel='x', font='Univers Next W1G',
                   ylabel=Markup('f(x) = x&#xb2;'), x_tick_res=0.5,
                   y_tick_res=1, markers=True, xlog=True, ylog=True)

    fh = open('output.svg', 'w')
    print >> fh, plot.construct()

    fh.close()
