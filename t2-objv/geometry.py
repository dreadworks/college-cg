#!/usr/bin/env python
# -*- coding: utf-8 -*-


import numpy as np


import parser
from util import LOG
log = LOG.out.info


"""

Geometry Definitions

Classes in this module are mainly
wrappers around parser objects. They
maintain the data used by OpenGL and
calculate missing (geometrical) data.

"""


class Polyhedron(object):

    def __str__(self):
        state = "Initialized" if hasattr(self, '_faces') else "Uninitialized"
        return "%s Polyhedron" % state

    def __init__(self):
        pass

    def load(self, fname):
        log("loading data from %s into Polyhedron" % fname)

        obj = parser.Obj(fname)
        self._faces = np.array([f for f in obj.faces()], 'f')
        # self._normals = obj.normals()

        log("loaded %d faces and %d normals" % (
            len(self.faces), 0))  # len(self.normals)))

    @property
    def faces(self):
        return self._faces

    @property
    def normals(self):
        return self._normals
