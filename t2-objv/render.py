#!/usr/bin/env python
# -*- coding: utf-8 -*-

# force floating point division
from __future__ import division

import math
import itertools
import numpy as np
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
    MODE_MOUSE_ZOOM = 1 << 0  # zoom middle mouse button
    MODE_MOUSE_MOVE = 1 << 1  # entity translation with right mouse button
    MODE_MOUSE_AROT = 1 << 2  # arcball rotation with left mouse button

    # map mutually exclusive coloring modes
    MODE_COLOR_ADD = True  # either add or subtract color
    MODE_COLOR_BG = 0      # background coloring
    MODE_COLOR_ENT = 1     # entity coloring

    def __init__(self, scene):
        self.modesMouse = (
            self.MODE_MOUSE_AROT,  # 0 => left mouse button
            self.MODE_MOUSE_ZOOM,  # 1 => middle mouse button
            self.MODE_MOUSE_MOVE)  # 2 => right mouse button

        self._modeMouse = 0       # initially no mouse button is pressed
        self._modeColor = self.MODE_COLOR_ENT
        self.scene = scene         # access to camera and entities

        # coloring offsets for
        # color recalculations
        o = 0.05
        self.clroffset = {
            's': (-o, -o, -o, 0),
            'w': (o, o, o, 0),
            'r': (o, 0, 0, 0),
            'g': (0, o, 0, 0),
            'b': (0, 0, o, 0)
        }

        # map k -> K with reversed effect
        for k, v in self.clroffset.items():
            self.clroffset[k.upper()] = map(lambda x: -1 * x, v)

    def reshape(self, width, height):
        trace('reshape called with %d, %d' % (width, height))
        self.scene.camera.ratio = width, height
        self.scene.repaint()

    def mouseClicked(self, btn, up, x, y):
        if up and self._modeMouse == self.MODE_MOUSE_AROT:
            for ent in self.scene.entities:
                ent.geometry.saveRotation()

        self._modeMouse = self._modeMouse ^ self.modesMouse[btn]
        trace('set mouse mode to ' + bin(self._modeMouse))

        if not up:
            # gets updated on mouseMove
            self._coords = (x, y)
            # stays fixed on mouseMove
            self._fixedCoords = (x, y)

    def mouseMove(self, *coords):
        camera = self.scene.camera
        dx, dy = [x - y for x, y in zip(coords, self._coords)]
        trace('mouseMove (%d, %d), offset (%d, %d)' % (x, y, dx, dy))

        #
        #   zoom in or out
        #
        if self._modeMouse & self.MODE_MOUSE_ZOOM:
            offset = camera.offset
            offset += dy / 100.
            camera.offset = offset

        #
        #   move object
        #
        if self._modeMouse & self.MODE_MOUSE_MOVE:
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
        if self._modeMouse & self.MODE_MOUSE_AROT:
            width, height = self.scene.camera.ratio
            r = self.scene.camera.ratioref / 2.

            def project_on_sphere(x, y, r):
                x, y = x - width / 2., height / 2. - y
                a = min(r ** 2, x ** 2 + y ** 2)
                z = math.sqrt(r ** 2 - a)
                l = math.sqrt(sum([q ** 2 for q in (x, y, z)]))
                return [q / l for q in (x, y, z)]

            start = project_on_sphere(*self._fixedCoords + (r, ))
            move = project_on_sphere(x, y, r)
            angle = math.acos(np.dot(start, move))
            axis = np.cross(start, move)

            for ent in self.scene.entities:
                ent.geometry.angle = angle
                ent.geometry.rotaxis = axis

        self._coords = coords
        self.scene.repaint()

    def keyPressed(self, key, x, y):
        #
        #   change colors
        #
        if key == 'q':
            self._modeColor = self._modeColor ^ 1
            log('changing background color mode to %d' % self._modeColor)

        if key in self.clroffset.keys():
            offset = self.clroffset[key]

            def sane(v):
                if v > 1:
                    return 1
                if v < 0:
                    return 0
                return v

            def mapclr(clr):
                clr = [sane(c + o) for c, o in zip(clr, offset)]
                trace('setting new color %s' % str(clr))
                return clr

            if self._modeColor == self.MODE_COLOR_BG:
                self.scene.background = mapclr(self.scene.background)
                print self.scene.background

            if self._modeColor == self.MODE_COLOR_ENT:
                for ent in self.scene.entities:
                    ent.material.ambient = mapclr(ent.material.ambient[1])
                    print ent.material.ambient

        #
        #   change perspective
        #
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
        self.material = Material()

    def render(self, camera):
        geometry = self.geometry
        trace('rendering entity %s at position %s' % (
            geometry, geometry.position))

        self.material.render()

        # configure geometry
        gl.glLoadIdentity()

        # do rotation, zoom and translation
        gl.glTranslate(*camera.translation)
        gl.glTranslate(*geometry.position)

        # save for plane
        gl.glPushMatrix()

        # arcball rotation
        gl.glMultMatrixf(self.geometry.rotation)

        # normalize
        gl.glScale(*geometry.rawScale)
        gl.glTranslate(*geometry.rawOffset)

        # configure appearance
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

    @mode.setter
    def mode(self, value):
        self._mode = value

    @property
    def geometry(self):
        return self._gm

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, value):
        self._material = value


class Light(object):

    _SOURCES = [
        gl.GL_LIGHT7, gl.GL_LIGHT6, gl.GL_LIGHT5,
        gl.GL_LIGHT4, gl.GL_LIGHT3, gl.GL_LIGHT2,
        gl.GL_LIGHT1, gl.GL_LIGHT0]

    def __init__(self):
        try:
            self._source = self._SOURCES.pop()
            log('creating light %s' % self._source)

            # set default values explicitly
            self.ambient = 0., 0., 0., 1.
            self.diffuse = 1., 1., 1., 1.
            self.specular = 1., 1., 1., 1.
            self.position = 0., 0., 0., 0.

        except Exception:
            raise RenderException('You can specify 8 lights, not more')

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = gl.GL_POSITION, pos

    @property
    def ambient(self):
        return self._ambient

    @ambient.setter
    def ambient(self, value):
        self._ambient = gl.GL_AMBIENT, value

    @property
    def diffuse(self):
        return self._diffuse

    @diffuse.setter
    def diffuse(self, value):
        self._diffuse = gl.GL_DIFFUSE, value

    @property
    def specular(self):
        return self._specular

    @specular.setter
    def specular(self, value):
        self._specular = gl.GL_SPECULAR, value

    def render(self):
        gl.glLight(self._source, *self.position)
        gl.glLight(self._source, *self.ambient)
        gl.glLight(self._source, *self.diffuse)
        gl.glLight(self._source, *self.specular)
        gl.glEnable(self._source)


class Material(object):

    def __init__(self):
        # set default values explicitly
        self.face = gl.GL_FRONT_AND_BACK
        self.ambient = .2, .2, .2, 1.
        self.diffuse = .8, .8, .8, 1.
        self.specular = 0., 0., 0., 1.
        self.emission = 0., 0., 0., 1.
        self.shininess = 0.

    @property
    def face(self):
        return self._face

    @face.setter
    def face(self, value):
        self._face = value

    @property
    def ambient(self):
        return self._ambient

    @ambient.setter
    def ambient(self, value):
        self._ambient = gl.GL_AMBIENT, value

    @property
    def diffuse(self):
        return self._diffuse

    @diffuse.setter
    def diffuse(self, value):
        self._diffuse = gl.GL_DIFFUSE, value

    @property
    def specular(self):
        return self._specular

    @specular.setter
    def specular(self, value):
        self._specular = gl.GL_SPECULAR, value

    @property
    def emission(self):
        return self._emission

    @emission.setter
    def emission(self, value):
        self._emission = gl.GL_EMISSION, value

    @property
    def shininess(self):
        return self._shininess

    @shininess.setter
    def shininess(self, value):
        # value in [0, 128]
        self._shininess = gl.GL_SHININESS, value

    def render(self):
        f = self.face
        gl.glMaterial(f, *self.ambient)
        gl.glMaterial(f, *self.diffuse)
        gl.glMaterial(f, *self.specular)
        gl.glMaterial(f, *self.emission)
        gl.glMaterial(f, *self.shininess)


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
        self._lights = []

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

    @background.setter
    def background(self, value):
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

    def createLight(self):
        light = Light()
        self._lights.append(light)
        return light

    def render(self):
        trace('rendering scene')

        gl.glClear(
            gl.GL_COLOR_BUFFER_BIT |
            gl.GL_DEPTH_BUFFER_BIT)

        gl.glClearColor(*self.background)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        # render lights
        for light in self._lights:
            light.render()

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
