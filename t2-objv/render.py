#!/usr/bin/env python
# -*- coding: utf-8 -*-

# force floating point division
from __future__ import division


import math
import itertools
import operator as op
from OpenGL import GL as gl
from OpenGL import GLU as glu

from util import Singleton
from util import LOG
log = LOG.out.info
trace = LOG.out.trace


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


class Handler(object):

    # map binary masks to the different mouse buttons
    MODE_ZOOM = 1 << 0  # zoom middle mouse button
    MODE_MOVE = 1 << 1  # entity translation with right mouse button
    MODE_AROT = 1 << 2  # arcball rotation with left mouse button

    # map mutually exclusive coloring modes
    MODE_CLR_BG = 0     # background coloring
    MODE_CLR_ENT = 1    # entity coloring

    def __init__(self, scene):
        self.modes = (
            self.MODE_AROT,  # 0 => left mouse button
            self.MODE_ZOOM,  # 1 => middle mouse button
            self.MODE_MOVE)  # 2 => right mouse button

        self._mode = 0       # initially no mouse button is pressed
        self.scene = scene   # access to camera and entities

    def reshape(self, width, height):
        trace('reshape called with %d, %d' % (width, height))
        self.scene.camera.ratio = width, height
        self.scene.repaint()

    def mouseClicked(self, btn, up, x, y):
        self._mode = self._mode ^ self.modes[btn]
        trace('set mouse mode to ' + bin(self._mode))

        if not up:
            self._coords = (x, y)

    def mouseMove(self, *coords):
        camera = self.scene.camera
        dx, dy = [x - y for x, y in zip(coords, self._coords)]
        trace('mouseMove (%d, %d), offset (%d, %d)' % (x, y, dx, dy))

        #
        #   zoom in or out
        #
        if self._mode & self.MODE_ZOOM:
            offset = camera.offset
            offset += dy / 100.
            camera.offset = offset

        #
        #   move object
        #
        if self._mode & self.MODE_MOVE:
            # the mouse movement must be translated
            # to the scene with regards to the zoom
            # and viewport ratio reference
            offset = camera.offset if camera.offset > 0.5 else 0.5
            f = camera.ratioref / 2. / offset

            for ent in self.scene.entities:
                x, y, z = ent.geometry.position
                ddx, ddy = map(lambda a: a / f, [dx, dy])
                ent.geometry.position = x + ddx, y - ddy, z

        #
        #   arcball rotation
        #
        if self._mode & self.MODE_AROT:
            pass  # TODO

        self._coords = coords
        self.scene.repaint()

    def keyPressed(self, key, x, y):
        if key == 'o':
            cam = self.scene.camera
            cam.mode = cam.ORTHOGONALLY

        if key == 'p':
            cam = self.scene.camera
            cam.mode = cam.PROJECTIVE

        self.scene.repaint()


#
#   ENTITIES
#
class Entity(object):

    def __init__(self, geometry):
        log('initializing entity')
        self._gm = geometry
        self.vbo = geometry.vbo

    def render(self, camera):
        geometry = self.geometry
        trace('rendering entity %s at position %s' % (
            geometry, geometry.position))

        # configure geometry
        gl.glLoadIdentity()

        # do rotation, zoom and translation
        gl.glTranslate(*camera.translation)
        gl.glTranslate(*geometry.position)

        # save for plane
        gl.glPushMatrix()

        # alter entities
        gl.glRotate(self._gm.angle, 0., 1., 0.)

        # normalize
        gl.glScale(*geometry.rawScale)
        gl.glTranslate(*geometry.rawOffset)

        # configure appearance
        gl.glColor(*geometry.color)
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


#
#   CAMERA
#
@Singleton
class Camera(list):

    ORTHOGONALLY = 0
    PROJECTIVE = 1

    def _reinitialize(self):
        try:  # check necessary props are set
            self.offset = self.offset
            self.mode
            if self.mode == self.PROJECTIVE:
                self.fow
        except:
            log('camera reinitialization attempt futile')
            return

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        if self.mode == self.PROJECTIVE:
            self._setProjective()

        if self.mode == self.ORTHOGONALLY:
            self._setOrthogonally()

        gl.glMatrixMode(gl.GL_MODELVIEW)
        self.offset = self.offset

    def _setOrthogonally(self):
        trace('set camera mode orthogonally')

        # apply scale by using the camera's offset
        # and scale based on the smallest side
        o, r = self.offset, self.asprat
        horiz, vert = (r * o, o) if r > 1 else (o, o / r)

        glu.gluOrtho2D(-horiz, horiz, -vert, vert)
        self.translation = 0.

    def _setProjective(self):
        trace('set camera mode projective (%f° field of view)' % self.fow)

        # apply scale later by translating
        # the object on the z-axis
        glu.gluPerspective(self.fow, self.asprat, .1, 100.)

        # translatation based on the offset
        alpha = math.radians(self.fow / 2)
        arcsin = 1 / math.sin(alpha)
        dx = math.sqrt(arcsin - 1) + 0.5

        # translation based on the aspect ratio
        ratio = 1. if self.asprat > 1 else self.asprat
        self.translation = -dx * (self.offset / ratio) - 2.

    def __init__(self):
        log('initializing camera')
        self._offset = 0.

    #
    #   PROPERTIES USED BY THE RENDERER
    #
    @property
    def translation(self):
        return self._translation

    @translation.setter
    def translation(self, trans):
        self._translation = 0., 0., trans

    #
    #   PROPERTIES
    #
    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        if self.mode == self.PROJECTIVE:
            minOffset = 0.

        if self.mode == self.ORTHOGONALLY:
            minOffset = 1.

        if offset < minOffset:
            offset = minOffset

        if offset != self.offset:
            trace('set camera offset to %f' % offset)
            self._offset = float(offset)
            self._reinitialize()

    @property
    def fow(self):
        return self._fow

    @fow.setter
    def fow(self, fow):
        self._fow = float(fow)

    @property
    def ratio(self):
        return self._ratio

    @property
    def asprat(self):
        return self._asprat

    @property
    def ratioref(self):
        return self._ratioref

    @ratio.setter
    def ratio(self, ratio):
        gl.glViewport(0, 0, *ratio)

        self._ratio = ratio
        self._asprat = op.truediv(*ratio)
        self._ratioref = min(ratio)

        self._reinitialize()
        trace('set camera ratio to %s, asprat: %f and ratioref: %d' % (
            self.ratio, self.asprat, self.ratioref))

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode
        self._reinitialize()


#
#   SCENE
#
@Singleton
class Scene(object):

    def __init__(self):
        log('initializing scene')
        self._entities = []

        log('initializing handler')
        self.evt = Handler(self)

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

        if value == 'smooth':
            gl.glShadeModel(gl.GL_SMOOTH)

        self._shading = value

    @property
    def repaint(self):
        return self._repaint

    @repaint.setter
    def repaint(self, value):
        self._repaint = value

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
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
    def camera(self, cam):
        self._camera = cam

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
        trace('rendering scene')

        gl.glClear(
            gl.GL_COLOR_BUFFER_BIT |
            gl.GL_DEPTH_BUFFER_BIT)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_NORMAL_ARRAY)

        # render all entities
        for ent in self._entities:
            ent.render(self.camera)

            # render floor under entity
            gl.glPopMatrix()
            gl.glTranslate(0., -1., 0.)

            gl.glBegin(gl.GL_LINE_LOOP)
            for x, z in itertools.product([-1, 1], repeat=2):
                gl.glVertex(x, 0, z)
            gl.glEnd()

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_NORMAL_ARRAY)

        gl.glFlush()
        self.callback()
