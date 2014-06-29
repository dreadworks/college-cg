#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging


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
LOG = Log('bezier')
