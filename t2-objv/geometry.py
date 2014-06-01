#!/usr/bin/env python
# -*- coding: utf-8 -*-


import math
import numpy as np
from OpenGL.arrays import vbo


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
        return self._name

    def __init__(self, obj):
        log("loading data from %s into Polyhedron" % obj.name())
        self._name = obj.name()
        # faces = np.array([f for f in obj.faces()], 'f')

        # calculate raw object offset
        bbx = np.vstack((
            obj.vertices.max(axis=0),
            obj.vertices.min(axis=0)))
        offset = (bbx[1] + bbx[0]) / -2.
        log('calculated offset of %s' % offset)

        # calculate raw object scale:
        # find the point with the greatest distance to
        # the bounding boxes center. The scale
        # factor of 1/scale gets divided by sqrt(2)
        # to consider a possible rotation of the object
        scale = abs((offset + bbx[0]).max())
        scale = math.sqrt(2) / (2 * scale)
        scale = [scale for _ in range(3)]
        log('calculated scale of %s' % scale[0])

        # set properties
        self._faces = obj.faces
        self._rawOffset = offset
        self._rawScale = scale

        # defaults
        self._angle = 0
        self._position = (0., 0., 0.)
        self._color = (1., 1., 1., 0.)

        log("loaded %d faces" % len(self.faces))

    #
    #   READ ONLY PROPERTIES
    #
    @property
    def vbo(self):
        return vbo.VBO(self.faces.flatten())

    @property
    def faces(self):
        return self._faces

    @property
    def rawScale(self):
        return self._rawScale

    @property
    def rawOffset(self):
        return self._rawOffset

    #
    #   CONFIGURABLE PROPERTIES
    #
    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value % 360

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
