#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging


"""

Utility Module.

"""


class Log(object):

    def __init__(self, name):
        logger = {}
        logger['stream'] = logging.StreamHandler()
        logger['stream'].setFormatter(
            logging.Formatter(
                ' '.join([
                    '[%(levelname)s]',
                    '%(asctime)s -',
                    '[%(name)s]',
                    '[%(threadName)s]',
                    '%(message)s']),
                '%H:%M:%S'))

        log = logging.getLogger(name)
        log.setLevel(logging.ERROR)
        log.addHandler(logger['stream'])
        self.out = log

    def setVerbose(self):
        self.out.setLevel(logging.INFO)
        self.out.info('logger mode set verbose')

# initialize
LOG = Log('objv')
