#!/usr/bin/env python
# -*- coding: utf-8 -*-


import math
import logging
import numpy as np


"""

Utility Module. Holds various
helper that wont fit into the
other modules.

"""


#
#   LOGGING
#
class Log(object):
    """

    Wraps logging.getLogger instances for easy use.

    """

    def __init__(self, name):
        logger = {}
        logger['stream'] = logging.StreamHandler()
        logger['stream'].setFormatter(
            logging.Formatter(
                ' '.join([
                    '[%(levelname)s]',
                    '%(asctime)s -',
                    '[%(filename)s:%(lineno)s]',
                    #'[%(funcName)s]',
                    '%(message)s']),
                '%H:%M:%S'))

        log = logging.getLogger(name)
        log.setLevel(logging.ERROR)
        log.addHandler(logger['stream'])
        self.out = log
        self.out.trace = self.out.debug

    def setVerbose(self):
        """
        Set all Log.out.info messages visible.

        :returns: None
        :rtype: None

        """
        self.out.setLevel(logging.INFO)
        self.out.info('logger mode set verbose')

    def setTrace(self):
        """
        Set all Log.out.trace messages visible

        :returns: None
        :rtype: None

        """
        self.out.setLevel(logging.DEBUG)
        self.out.trace('logger mode set to trace mode')

# initialize
LOG = Log('objv')


#
#   SINGLETON
#
#   (from stackoverflow.com/questions/42558/python-and-the-singleton-pattern)
class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.
    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.
        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


#
#   COLOR
#
class Color(list):
    """

    Easy to use color definitions. Every
    color instance is a list of four elements
    whose elements range from 0 to 1. The elements
    describe r, g, b and alpha of a color. Various
    setter exist to transform arbitrary definitions
    into this uniform format.

    """

    def _clear(self):
        """
        Removes the current color definition

        :returns: None
        :rtype: None

        """
        del self[0:len(self)]

    def __init__(self):
        """
        Create a new color instance.
        Standard color value of new instances
        is [0, 0, 0, 0]

        :returns: self
        :rtype: util.Color

        """
        self += [0., 0., 0., 0.]

    def hsla(self, h, s, l, a):
        """
        Provide hue, saturation, lightness and
        alpha and transform them into the unified
        color format

        :param h: Colors hue value [0, 360]
        :param s: Saturation [0, 1]
        :param l: Lightness [0, 1]
        :param a: Opacity [0, 1]
        :returns: self
        :rtype: util.Color

        """
        self._clear()

        s, l, a = map(float, (s, l, a))
        h = math.radians(h)
        q = math.sqrt

        p = np.array([
            [q(2. / 3.) * s * math.cos(h)],
            [q(2. / 3.) * s * math.sin(h)],
            [(4. * l) / q(3)]
        ])

        T = np.array([
            [   2. / q(6),           0., 1. / q(3)],
            [-(1. / q(6)),    1. / q(2), 1. / q(3)],
            [-(1. / q(6)), -(1. / q(2)), 1. / q(3)]
        ])

        rgba = np.append(T.dot(p).flatten(), a)
        self.rgba(*rgba)
        return self

    def rgba(self, r, g, b, a):
        """
        Provide red, green, blue and alpha
        color values and transform them into the
        unified color format.

        :param r: Red value [0, 255]
        :param g: Green value [0, 255]
        :param b: Blue value [0, 255]
        :param a: Alpha value [0, 1]
        :returns: self
        :rtype: util.Color

        """
        self._clear()

        rgb = r, g, b
        for v in rgb:
            self.append(v / float(0xff))

        self.append(a)
        return self

    def hex(self, code):
        """
        Provide a hexadecimal color code.
        It's just a shortcut for rgba.
        Format: 0xrrggbbaa; r, g, b, a in [0x0, 0xff]

        :param code: Hexadecimal color value code
        :returns: self
        :rtype: util.Color

        """
        self._clear()

        for offset in range(0, 32, 8):
            v = (code >> offset) & 0xff
            self.insert(0, v / float(0xff))

        return self
