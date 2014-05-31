#!/usr/bin/env python
# -*- coding: utf-8 -*-


import math
from OpenGL import GL as gl
from OpenGL import GLU as glu

from util import Singleton
from util import LOG
log = LOG.out.info


"""

Rendering Module.

Handles OpenGL directives,
initializes and changes the scene.

"""


class RenderException(Exception):

    def __str__(self):
        return self.msg

    def __init__(self, msg):
        self.msg = msg


class Entity(object):

    def __init__(self, geometry):
        log('initializing entity')
        self._gm = geometry
        self.vbo = geometry.vbo

    def render(self, camera):
        # log('rendering entity %s' % self._gm)

        # configure geometry
        gl.glLoadIdentity()

        # do rotation, zoom and translation
        gl.glTranslate(0., 0., camera.translation)
        gl.glRotate(self._gm.angle, 0., 1., 0.)

        # normalize
        gl.glScale(*self._gm.rawScale)
        gl.glTranslate(*self._gm.rawOffset)

        # configure appearance
        gl.glColor(*self._gm.color)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, self.mode)

        # render vertex/normal buffer
        self.vbo.bind()

        # Data in the vbo is saved as follows:
        # [v₀, vn₀, v₁, vn₁, v₂, vn₂, ...]
        # where every v and vn is a 32bit (4 byte) float.
        # So the vertex pointer maintains 3 * 4 (12) byte
        # vertices, followed by 3 * 4 (12) byte surface normals.
        # The offset between every v is 12 byte and the
        # pointer to the first normal has an offset of 12
        # byte to the beginning of the whole buffer.
        gl.glVertexPointer(3, gl.GL_FLOAT, 24, self.vbo)
        gl.glNormalPointer(gl.GL_FLOAT, 24, self.vbo + 12)

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(self.vbo.data))
        self.vbo.unbind()

    @property
    def mode(self):
        return self._mode

    @property
    def geometry(self):
        return self._gm

    @mode.setter
    def mode(self, value):
        self._mode = value


@Singleton
class Camera(list):

    ORTHOGONALLY = 0
    PROJECTIVE = 1

    def _setOrthogonally(self):
        log('set camera mode orthogonally')
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        # apply scale by using the raw offset
        glu.gluOrtho2D(
            -self.offset, self.offset,
            -self.offset, self.offset)

        self._translation = 0
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def _setProjective(self):
        if self._fow is None:
            raise RenderException('You must set the fow first.')

        log('set camera mode projective (%f° field of view)' % self.fow)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        # apply scale later by translating
        # the object on the z-axis
        glu.gluPerspective(self.fow, 1., .1, 100.)

        # translatation of the object based
        # on the given field of view and offset:
        alpha = math.radians(self.fow / 2)
        arcsin = 1 / math.sin(alpha)
        dx = math.sqrt(arcsin - 1) + 0.5

        self._translation = -dx * self.offset
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def __init__(self):
        log('initializing camera')
        self._fow = None

    #
    #   PROPERTIES USED BY THE RENDERER
    #
    @property
    def translation(self):
        return self._translation

    #
    #   PROPERTIES
    #
    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        log('set camera offset to %f' % offset)
        self._offset = float(offset)

    @property
    def fow(self):
        return self._fow

    @fow.setter
    def fow(self, fow):
        self._fow = float(fow)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode == self.PROJECTIVE:
            self._setProjective()

        if mode == self.ORTHOGONALLY:
            self._setOrthogonally()

        self._mode = mode


@Singleton
class Scene():

    def __init__(self):
        log('initializing scene')
        self._entities = []

        gl.glEnable(gl.GL_NORMALIZE)
        gl.glEnable(gl.GL_DEPTH_TEST)

    @property
    def shading(self):
        return self._shading

    def setShading(self, value):
        log('setting scene shader to %s' % value)

        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)

        if value == 'flat':
            gl.glShadeModel(gl.GL_FLAT)

        if value == 'gouraud':
            gl.glShadeModel(gl.GL_SMOOTH)

        self._shading = value

    @property
    def callback(self):
        return self._callback

    def setCallback(self, value):
        self._callback = value

    @property
    def background(self):
        return self._background

    def setBackground(self, value):
        gl.glClearColor(*value)
        self._background = value

    @property
    def camera(self):
        return self._camera

    @camera.setter
    def camera(self, value):
        self._camera = value

    @property
    def entities(self):
        return self._entities

    def addEntity(self, polyhedron):
        log('adding polyhedron "%s" to scene' % polyhedron)
        ent = Entity(polyhedron)
        ent.mode = gl.GL_LINE if self.shading == 'grid' else gl.GL_FILL
        self._entities.append(ent)
        return ent

    def render(self):
        # log('rendering scene')
        gl.glClear(
            gl.GL_COLOR_BUFFER_BIT |
            gl.GL_DEPTH_BUFFER_BIT)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_NORMAL_ARRAY)

        # render all entities
        for ent in self._entities:
            ent.render(self.camera)

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_NORMAL_ARRAY)
        self.callback()
