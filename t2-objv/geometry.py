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
        faces = np.array([f for f in obj.faces()], 'f')
        points = np.array(obj.vertices, 'f')

        # calculate raw object offset
        bbx = np.vstack((
            points.max(axis=0),
            points.min(axis=0)))
        offset = (bbx[1] + bbx[0]) / -2
        log('calculated offset of %s' % offset)

        # calculate raw object scale
        scale = 1 / abs((offset + bbx[1]).max())
        scale = [scale for _ in range(3)]
        log('calculated scale of %s' % scale)

        # set properties
        self._faces = faces
        self._rawOffset = offset
        self._rawScale = scale

        # self._normals = obj.normals()

        log("loaded %d faces and %d normals" % (
            len(self.faces), 0))  # len(self.normals)))

    @property
    def faces(self):
        return self._faces

    @property
    def normals(self):
        return self._normals

    @property
    def rawScale(self):
        return self._rawScale

    @property
    def rawOffset(self):
        return self._rawOffset
