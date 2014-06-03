#!/usr/bin/env python
# -*- coding: utf-8 -*-


import math
import logging
import numpy as np


"""

Utility Module.

"""


#
#   LOGGING
#
class Log(object):

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
        self.out.setLevel(logging.INFO)
        self.out.info('logger mode set verbose')

    def setTrace(self):
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

    def _clear(self):
        del self[0:len(self)]

    def __init__(self):
        self += [0., 0., 0.]

    def hsla(self, h, s, l, a):
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

    def rgba(self, r, g, b, a):
        # r, g, b in [0, 255], a in [0, 1]
        self._clear()

        rgb = r, g, b
        for v in rgb:
            self.append(v / float(0xff))

        self.append(a)
        return self

    def hex(self, code):
        self._clear()

        for offset in range(0, 32, 8):
            v = (code >> offset) & 0xff
            self.insert(0, v / float(0xff))

        return self
