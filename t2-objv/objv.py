#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys


import geometry
from util import LOG as logger


"""

Main Module, TODO docs

"""


def main(argv):
    logger.setVerbose()
    if len(argv) < 2:
        print("Usage: objv filename")
        return

    polyhedron = geometry.Polyhedron()
    polyhedron.load(argv[1])
    print("got polyhedron: %s" % str(polyhedron))

if __name__ == '__main__':
    main(sys.argv)
