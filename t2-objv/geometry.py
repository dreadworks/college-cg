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


class GeometryException(Exception):

    def __str__(self):
        return self.msg

    def __init__(self, msg):
        self.msg = msg


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
        self.angle = 0
        self.rotaxis = 0., 1., 0.
        self.position = 0., 0., 0.
        self._lastRotmat = np.identity(4)

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

    @property
    def rotation(self):
        try:
            self.angle, self.rotaxis
        except:
            raise GeometryException(
                'Angle and rotaxis must be set to use rotate')

        s, c = math.sin(self.angle), math.cos(self.angle)
        l = np.linalg.norm(self.rotaxis)
        x, y, z = [q / l for q in self.rotaxis]
        mc = 1 - c

        r = np.matrix([
            [(x * x * mc + c), (x * y * mc - z * s), (x * z * mc + y * s), 0],
            [(x * y * mc + z * s), (y * y * mc + c), (y * z * mc - x * s), 0],
            [(x * z * mc - y * s), (y * z * mc + x * s), (z * z * mc + c), 0],
            [0, 0, 0, 1]])

        # column major for OpenGL
        return self._lastRotmat * r.transpose()

    def saveRotation(self):
        self._lastRotmat = self.rotation
        self.angle = 0

    #
    #   CONFIGURABLE PROPERTIES
    #
    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value % 360

    @property
    def rotaxis(self):
        return self._rotaxis

    @rotaxis.setter
    def rotaxis(self, value):
        self._rotaxis = value

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
