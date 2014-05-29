#!/usr/bin/env python
# -*- coding: utf-8 -*-


from OpenGL import GL as gl


from util import Singleton
from util import LOG
log = LOG.out.info


"""

Rendering Module.

Handles OpenGL directives,
initializes and changes the scene.

"""


class Entity(object):

    def __init__(self, geometry):
        log('initializing entity')
        self._gm = geometry
        self.vbo = geometry.vbo

    def render(self):
        # log('rendering entity %s' % self._gm)

        # configure geometry
        gl.glLoadIdentity()
        gl.glScale(*self._gm.rawScale)
        gl.glTranslate(*self._gm.rawOffset)
        gl.glRotate(self._gm.angle, 0., 1., 0.)

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


class Camera(object):

    def __init__(self):
        log('creating camera')


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

        if value == 'flat':
            gl.glShadeModel(gl.GL_FLAT)

        if value == 'gouraud':
            gl.glEnable(gl.GL_LIGHTING)
            gl.glEnable(gl.GL_LIGHT0)

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
            ent.render()

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_NORMAL_ARRAY)
        self.callback()
