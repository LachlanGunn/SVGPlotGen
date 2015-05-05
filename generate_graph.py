#!/usr/bin/env python

import os
import math
import numpy as np

from genshi.template import TemplateLoader
from genshi.core import Markup

class SVGPlot(object):

    def __init__(self,
                 width=58, height=82,
                 axis_width=46, axis_height=46,
                 axis_left=8.4, axis_top=3,
                 font='Myriad Pro', font_size=10,
                 xmin=0.0, xmax=1.0, x_tick_res=0.2,
                 ymin=0.0, ymax=1.0, y_tick_res=0.2,
                 data=[], xlabel = '', ylabel = '',
                 inkscape_length_fix=True):

        self.width = width
        self.height = height
        self.axis_width = axis_width
        self.axis_height = axis_height
        self.axis_left = axis_left
        self.axis_top = axis_top
        self.font = font
        self.font_size = font_size
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.x_tick_res = x_tick_res
        self.y_tick_res = y_tick_res
        self.data = data
        self.inkscape_length_fix=inkscape_length_fix

    def construct(self):

        x_scale = self.axis_width/(self.xmax-self.xmin)
        y_scale = self.axis_height/(self.ymax-self.ymin)

        pixels_per_millimeter = 3.7795
        if self.inkscape_length_fix:
            pixels_per_millimeter *= 90.0/96

        axis_origin = (self.axis_left, self.axis_top+self.axis_height)

        # M 15 57 L 30 52 L 67 5
        series_list = []
        for series in self.data:
            x = np.array(series[0])
            y = np.array(series[1])

            x_transformed = ( x*x_scale + axis_origin[0])*pixels_per_millimeter
            y_transformed = (-y*y_scale + axis_origin[1])*pixels_per_millimeter

            coordinates = ['%f %f' % p for p in zip(x_transformed, y_transformed)]

            series_list.append('M ' + ' L'.join(coordinates))

        xticks = []
        yticks = []

        start_tick = math.ceil(self.xmin/self.x_tick_res)*self.x_tick_res

        for tick in np.arange(start_tick, self.xmax+1e-9, self.x_tick_res):
            position = self.axis_left + tick*x_scale

            if self.xmin < tick < self.xmax:
                style = 'display'
            else:
                style = 'hide'

            xticks.append({'position': position,
                           'label': tick,
                           'style': style})

        start_tick = math.ceil(self.ymin/self.y_tick_res)*self.y_tick_res

        for tick in np.arange(start_tick, self.ymax+1e-9, self.y_tick_res):
            position = self.axis_top+self.axis_height - tick*y_scale

            if self.ymin < tick < self.ymax:
                style = 'display'
            else:
                style = 'hide'

            yticks.append({'position': position,
                           'label': tick,
                           'style': style})


        options = {
                'svg_width':   self.width,
                'svg_height':  self.height,
                'axis_width':  self.axis_width,
                'axis_height': self.axis_height,
                'axis_left':   self.axis_left,
                'axis_top':    self.axis_top,
                'font':        self.font,
                'font_size':   self.font_size,
                'xticks':      xticks,
                'yticks':      yticks,
                'series':      series_list,
                'xlabel':      self.xlabel,
                'ylabel':      self.ylabel
            }

        loader = TemplateLoader(
            os.path.join(os.path.dirname(__file__), 'templates'),
            auto_reload=True
        )
        template = loader.load('template.svg')
        return template.generate(**options).render('xml')

if __name__ == '__main__':

    x = np.linspace(0,2,100)
    y = x**2

    plot = SVGPlot(data=[(x, y)], xlabel='x', font='Univers Next W1G', ylabel=Markup('f(x) = x&#xb2;'), xmin=0,xmax=2,ymin=0,ymax=4,x_tick_res=0.5,y_tick_res=1)

    fh = open('output.svg', 'w')
    print >>fh, plot.construct()

    fh.close()