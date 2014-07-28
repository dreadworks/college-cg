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
    """

    A polyhedron is a mesh of triangles.
    It is easily renderable by OpenGL as it saves
    its data into an vertex buffer object.

    """

    def __str__(self):
        return self._name

    def __init__(self, obj):
        """
        Create a new Polyhedron. The obj must
        provide a name, vertices, normals and
        faces as raw data.

        :param obj: Geometrical and topological data
        :returns: self
        :rtype: geometry.Polyhedron

        """
        log("loading data from %s into Polyhedron" % obj.name())
        self._name = obj.name()

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
        """
        Vertex Buffer Object for OpenGL.
        Data is saved as repeated v, vn pairs.

        :returns: The vbo
        :rtype: OpenGL.arrays.vbo.VBO

        """
        return vbo.VBO(self.faces.flatten())

    @property
    def faces(self):
        """
        Returns a list of (v, vn) tuples where
        v is a vertex and vn the surface normal
        at that vertex.

        :returns: The objects faces
        :rtype: list

        """
        return self._faces

    @property
    def rawScale(self):
        """
        Describes the scale factor that is
        needed to scale the objects bounding
        box so that it has an edge length of 2.

        :returns: The normalization scale factor.
        :rtype: float

        """
        return self._rawScale

    @property
    def rawOffset(self):
        """
        Describes the offset of the bounding
        box' center from the center of "the"
        world coordinate systems origin.

        :returns: Offset from the origin
        :rtype: iterable
        """
        return self._rawOffset

    @property
    def rotation(self):
        """
        Returns a 4x4 Matrix in column major
        form describing the rotation of the
        object based on its angle and rotation
        axis.

        :returns: The rotation matrix
        :rtype: numpy.matlib.matrix

        """

        try:
            self.angle, self.rotaxis
        except:
            raise GeometryException(
                'Angle and rotaxis must be set to use rotate')

        l = np.linalg.norm(self.rotaxis)
        if l == 0:
            return self._lastRotmat

        s, c = math.sin(self.angle), math.cos(self.angle)
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
        """
        Saves the current rotation matrix for
        future transformations.

        :returns: None
        :rtype: None

        """

        self._lastRotmat = self.rotation
        self.angle = 0

    #
    #   CONFIGURABLE PROPERTIES
    #
    @property
    def angle(self):
        """
        Returns the current angle.

        :returns: The rotation angle
        :rtype: float

        """
        return self._angle

    @angle.setter
    def angle(self, value):
        """
        Set the angle. The provided value
        gets truncated by calculating the
        modulus of 360. Setting this argument
        is only useful in conjunction with
        the rotaxis property.

        :param value: Arbitrary number
        :returns: None
        :rtype: None

        """
        self._angle = value % 360

    @property
    def rotaxis(self):
        """
        The rotation axis.

        :returns: A three dimensional vector
        :rtype: list

        """
        return self._rotaxis

    @rotaxis.setter
    def rotaxis(self, value):
        """
        Set the rotation axis. Setting this
        argument is only useful in conjunction
        with the angle property.

        :param value: Three dimensional vector
        :returns: None
        :rtype: None

        """
        self._rotaxis = value

    @property
    def position(self):
        """
        The objects position.

        :returns: Three dimensional point
        :rtype: iterable

        """
        return self._position

    @position.setter
    def position(self, position):
        """
        Set the objects position.

        :param position: Three dimensional point
        :returns: None
        :rtype: None

        """
        self._position = position
