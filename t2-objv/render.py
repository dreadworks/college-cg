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

render.Handler
  Reacts on GUI-Events. Changes the state
  of the scene or entities and requests
  a repaint.

render.Entity:
  Wrapper for geometry. Handle geometry related
  rendering and optional shadow creation.

render.Material:
  Entity material.

render.Light:
  Global scene lighting.

render.Camera:
  Viewport and zoom.

render.Scene:
  Rendering dispatcher. Maintains "global"
  scene configuration.

"""


class RenderException(Exception):

    def __str__(self):
        return self.msg

    def __init__(self, msg):
        self.msg = msg


class Handler(object):
    """

    All handler for GUI-Events are handled within
    this class. The scene and its entities are updated
    accordingly and a repainting request is issued.

    """

    # map binary masks to the different mouse buttons
    MODE_MOUSE_ZOOM = 1 << 0  # zoom middle mouse button
    MODE_MOUSE_MOVE = 1 << 1  # entity translation with right mouse button
    MODE_MOUSE_AROT = 1 << 2  # arcball rotation with left mouse button

    # map mutually exclusive coloring modes
    MODE_COLOR_ADD = True  # either add or subtract color
    MODE_COLOR_BG = 0      # background coloring
    MODE_COLOR_ENT = 1     # entity coloring

    def _projectOnSphere(self, x, y):
        """
        Takes x, y viewport coordinates and
        projects them (based on the viewport)
        onto a sphere spanning the visible
        area of the scene. Gets used to determine
        axis and angle of the arcball rotation.

        :param x: viewport x-coordinate
        :param y: viewport y-coordinate
        :returns: Three dimensional point
        :rtype: list

        """
        
        width, height = self.scene.camera.ratio
        r = self.scene.camera.ratioref / 2.
        x, y = x - width / 2., height / 2. - y

        a = min(r ** 2, x ** 2 + y ** 2)
        z = math.sqrt(r ** 2 - a)
        l = math.sqrt(sum([q ** 2 for q in (x, y, z)]))
        return [q / l for q in (x, y, z)]

    def __init__(self, scene):
        """
        Initializes the handler. Takes a scene
        whose properties are changed upon registering
        events.

        :param scene: render.Scene instance
        :returns: self
        :rtype: render.Handler

        """
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
        """
        Called when the viewport size changes.

        :param width: New viewport width
        :param height: New viewport height
        :returns: None
        :rtype: None

        """
        trace('reshape called with %d, %d' % (width, height))
        self.scene.camera.ratio = width, height
        self.scene.repaint()

    def mouseClicked(self, btn, up, x, y):
        """
        Event fired when a mouse button gets
        pressed or released.

        :param btn: 0, 1, 2 as mapped by GLUT
        :param up: 0 or 1 if pressed or released
        :param x: Cursors x-coordinate
        :param y: Cursors y-coordinate
        :returns: None
        :rtype: None

        """
        if up and self._modeMouse == self.MODE_MOUSE_AROT:
            for ent in self.scene.entities:
                ent.geometry.saveRotation()

        self._modeMouse = self._modeMouse ^ self.modesMouse[btn]
        trace('set mouse mode to ' + bin(self._modeMouse))

        if not up:
            # gets updated on mouseMove
            self._coords = (x, y)
            self._arotStart = self._projectOnSphere(x, y)

    def mouseMoved(self, *coords):
        """
        Called when a mouse button is pressed and
        the cursor gets moved around.

        :returns: None
        :rtype: None

        """
        camera = self.scene.camera
        dx, dy = [x - y for x, y in zip(coords, self._coords)]
        x, y = coords  # x and y leak into the function scope!
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
            start = self._arotStart
            move = self._projectOnSphere(x, y)
            angle = math.acos(np.dot(start, move))
            axis = np.cross(start, move)

            for ent in self.scene.entities:
                ent.geometry.angle = angle
                ent.geometry.rotaxis = axis

        self._coords = coords
        self.scene.repaint()

    def keyPressed(self, key, x, y):
        """
        Called when a key gets pressed.

        :param key: Key on the keyboard
        :param x: Cursors x-coordinate
        :param y: Cursors y-coordinate
        :returns: None
        :rtype: None

        """
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

            if self._modeColor == self.MODE_COLOR_ENT:
                for ent in self.scene.entities:
                    ent.material.ambient = mapclr(ent.material.ambient[1])

        #
        #   change perspective
        #
        if key == 'o':
            cam = self.scene.camera
            cam.mode = cam.ORTHOGONALLY

        if key == 'p':
            cam = self.scene.camera
            cam.mode = cam.PROJECTIVE

        if key == 'h':
            self.scene.toggleShadow()

        self.scene.repaint()


#
#   ENTITIES
#
class Entity(object):
    """

    Entities wrap objects from the geometry.py module.
    They must provide a rendering method and carefully
    maintain their MODELVIEW stack. Entities have Materials
    to alter their appearance. Geometrical definitions like
    rotation and translatation are defined in their geometry.
    Entities render a shadow optionally.

    """

    def __init__(self, geometry):
        """
        Create a new entity. A geometry.* instances
        must be provided that maintains all geometrical
        data and a vbo.

        :param geometry: geometry.* instance
        :returns: self
        :rtype: render.Entity

        """
        log('initializing entity')
        self._gm = geometry
        self.vbo = geometry.vbo
        self.material = Material()
        self.shadow = 0., 0., 0., 0.

    def _renderVertices(self):
        """
        Takes the geometries vertex buffer
        and issues the OpenGL drawing command.

        :returns: None
        :rtype: None

        """
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

    def _renderShadow(self, light):
        """
        Transforms the object onto the x/z-plane
        as the objects shadow.

        :param light: Light source that defines the shadow
        :returns: None
        :rtype: None

        """
        geometry = self.geometry

        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_LIGHTING)

        x, y, z = light.position[1]
        pj = 1. / -y

        T = np.transpose([
            [1., 0., 0., 0.],
            [0., 1., 0., 0.],
            [0., 0., 1., 0.],
            [0., pj, 0., 0.]
        ])

        # move and scale according to the
        # lights position
        dist = np.linalg.norm((x, y, z))
        gl.glTranslate(-x * dist, -1., -z * dist)

        # translate into center, project
        # on the z/x-plane and move back
        gl.glTranslate(x, y, z)
        gl.glMultMatrixf(T)
        gl.glTranslate(-x, -y, -z)

        # rotate and normalize
        gl.glMultMatrixf(self.geometry.rotation)
        gl.glScale(*geometry.rawScale)
        gl.glTranslate(*geometry.rawOffset)

        # set uniform color and render
        # the projection
        gl.glColor(*self.shadow)
        self._renderVertices()

        # restore
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_DEPTH_TEST)

    def render(self, camera, light=None):
        """
        Main rendering method. Gets called
        by the scene for every rendering cicle.

        :param camera: render.Camera instance
        :param light: optional render.Light instance
        :returns: None
        :rtype: None

        """
        geometry = self.geometry

        trace('rendering entity %s at position %s' % (
            geometry, geometry.position))

        self.material.render()
        gl.glLoadIdentity()

        # do rotation, zoom and translation
        gl.glTranslate(*camera.translation)
        gl.glTranslate(*geometry.position)

        gl.glPushMatrix()  # for plane

        # render shadow
        if light is not None:
            gl.glPushMatrix()
            self._renderShadow(light, geometry)
            gl.glPopMatrix()

        gl.glMultMatrixf(self.geometry.rotation)
        gl.glScale(*geometry.rawScale)
        gl.glTranslate(*geometry.rawOffset)

        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, self.mode)
        self._renderVertices()

    @property
    def mode(self):
        """
        The rendering mode.

        :returns: OpenGL rendering mode
        :rtype: gl.glPolygonMode parameter

        """
        return self._mode

    @mode.setter
    def mode(self, value):
        """
        Set the rendering mode. The parameter
        must be suitable for gl.glPolygonMode

        :param value: gl.glPolygonMode
        :returns: None
        :rtype: None

        """
        self._mode = value

    @property
    def geometry(self):
        """
        Returns the geometry for the entity.

        :returns: The entities geometry
        :rtype: geometry.*

        """
        return self._gm

    @property
    def material(self):
        """
        Returns the entites material.

        :returns: Material instance
        :rtype: render.Material

        """
        return self._material

    @material.setter
    def material(self, value):
        """
        Set the entities material.

        :param value: render.Material instance
        :returns: None
        :rtype: None

        """
        self._material = value

    @property
    def shadow(self):
        """
        Returns the objects shadow color.

        :returns: 4 dimensional point
        :rtype: list

        """
        return self._shadow

    @shadow.setter
    def shadow(self, value):
        """
        Set the objects shadow color.

        :param value: 4 dimensional point
        :returns: None
        :rtype: None

        """
        self._shadow = value


class Light(object):
    """

    Wrapper class around gl.glLight. A maximum of
    8 lights may be instanciated.

    """

    _SOURCES = [
        gl.GL_LIGHT7, gl.GL_LIGHT6, gl.GL_LIGHT5,
        gl.GL_LIGHT4, gl.GL_LIGHT3, gl.GL_LIGHT2,
        gl.GL_LIGHT1, gl.GL_LIGHT0]

    def __init__(self):
        """
        Upon initialization one of gl.GL_LIGHT[0-8] gets used.
        All properties are set to the OpenGL standard.

        :returns: self
        :rtype: render.Light

        """
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
        """
        Get the lights position

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._position

    @position.setter
    def position(self, pos):
        """
        Set the lights position

        :param pos: Three dimensional point
        :returns: None
        :rtype: None

        """
        self._position = gl.GL_POSITION, pos

    @property
    def ambient(self):
        """
        Get the lights ambient share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._ambient

    @ambient.setter
    def ambient(self, value):
        """
        Set the lights ambient share.

        :param value: Three dimensional point
        :returns: None
        :rtype: None

        """
        self._ambient = gl.GL_AMBIENT, value

    @property
    def diffuse(self):
        """
        Get the lights diffuse share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._diffuse

    @diffuse.setter
    def diffuse(self, value):
        """
        Set the lights diffuse share.

        :param value: Three dimensional point
        :returns: None
        :rtype: None

        """
        self._diffuse = gl.GL_DIFFUSE, value

    @property
    def specular(self):
        """
        Get the lights specular share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._specular

    @specular.setter
    def specular(self, value):
        """
        Set the lights specular share.

        :param value: Three dimensional point
        :returns: None
        :rtype: None

        """
        self._specular = gl.GL_SPECULAR, value

    def render(self):
        """
        Gets called every rendering cicle. Updates
        the light based on its properties.

        :returns: None
        :rtype: None

        """
        gl.glLight(self._source, *self.position)
        gl.glLight(self._source, *self.ambient)
        gl.glLight(self._source, *self.diffuse)
        gl.glLight(self._source, *self.specular)
        gl.glEnable(self._source)


class Material(object):
    """

    Wrapper class around gl.glMaterial.

    """

    def __init__(self):
        """
        Create a material for use by render.Entity.
        Properties are set based on the OpenGL standards.

        :returns: self
        :rtype: render.Material

        """

        self.face = gl.GL_FRONT_AND_BACK
        self.ambient = .2, .2, .2, 1.
        self.diffuse = .8, .8, .8, 1.
        self.specular = 0., 0., 0., 1.
        self.emission = 0., 0., 0., 1.
        self.shininess = 0.

    @property
    def face(self):
        """
        The face to render the material on.

        :returns: OpenGL face directive
        :rtype: OpenGL constant

        """
        return self._face

    @face.setter
    def face(self, value):
        """
        Set the face to render the material on.
        Accepts gl.GL_FRONT, gl.GL_BACK and
        gl.GL_FRONT_AND_BACK (standard).

        :param value: OpenGL face directive
        :returns: None
        :rtype: None

        """
        self._face = value

    @property
    def ambient(self):
        """
        Get the materials ambient share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._ambient

    @ambient.setter
    def ambient(self, value):
        """
        Sets the materials ambient share.

        :param value: A three dimensional point
        :returns: None
        :rtype: None

        """
        self._ambient = gl.GL_AMBIENT, value

    @property
    def diffuse(self):
        """
        Get the materials diffuse share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._diffuse

    @diffuse.setter
    def diffuse(self, value):
        """
        Sets the materials ambient share.

        :param value: A three dimensional point
        :returns: None
        :rtype: None

        """
        self._diffuse = gl.GL_DIFFUSE, value

    @property
    def specular(self):
        """
        Get the materials specular share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._specular

    @specular.setter
    def specular(self, value):
        """
        Sets the materials specular share.

        :param value: A three dimensional point
        :returns: None
        :rtype: None

        """
        self._specular = gl.GL_SPECULAR, value

    @property
    def emission(self):
        """
        Get the materials emission share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._emission

    @emission.setter
    def emission(self, value):
        """
        Sets the materials emission share.

        :param value: A three dimensional point
        :returns: None
        :rtype: None

        """
        self._emission = gl.GL_EMISSION, value

    @property
    def shininess(self):
        """
        Get the materials shininess share.

        :returns: OpenGL directive and a three dimensional point
        :rtype: tuple

        """
        return self._shininess

    @shininess.setter
    def shininess(self, value):
        """
        Sets the materials shininess share.
        Accepts values in [0, 128]

        :param value: A three dimensional point
        :returns: None
        :rtype: None

        """
        self._shininess = gl.GL_SHININESS, value

    def render(self):
        """
        Gets called upon every rendering cicle of the entity.
        Updates the material properties in OpenGL.

        :returns: None
        :rtype: None

        """
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
    """

    Maintains all viewport and zooming related configurations.
    The camera mode can be set to be orthogonally or projective
    respectively.

    """

    ORTHOGONALLY = 0
    PROJECTIVE = 1

    def _reinitialize(self):
        """
        Helper function to reinitialize the
        camera if a property got set. Checks
        if all required properties are set first.

        :returns: None
        :rtype: None

        """
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
        """
        Set the camera mode orthogonally.
        The z-axis gets effectively cut
        and no peception of perspective
        between multiple entities remains.

        :returns: None
        :rtype: None

        """
        trace('set camera mode orthogonally')

        # apply scale by using the camera's offset
        # and scale based on the smallest side
        o, r = self.offset, self.asprat
        horiz, vert = (r * o, o) if r > 1 else (o, o / r)

        glu.gluOrtho2D(-horiz, horiz, -vert, vert)
        self.translation = 0.

    def _setProjective(self):
        """
        Set the camera mode projective.
        A perspective distortion is applied
        and a three dimensional impression
        originates.

        :returns: None
        :rtype: None

        """
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
        """
        Initialize the camera singleton.

        :returns: self
        :rtype: render.Camera

        """
        log('initializing camera')
        self._offset = 0.

    #
    #   PROPERTIES USED BY THE RENDERER
    #
    @property
    def translation(self):
        """
        Translate objects "filmed" by the camera
        based on the mode so that they stay inside
        the frustum. Needed to apply the offset
        when the camera mode is set projective.

        :returns: Three dimensional point
        :rtype: tuple

        """
        return self._translation

    @translation.setter
    def translation(self, trans):
        """
        Set the z-component of the
        translation vector.

        :param trans: float describing the offset
        :returns: None
        :rtype: None

        """
        self._translation = 0., 0., trans

    #
    #   PROPERTIES
    #
    @property
    def offset(self):
        """
        Positive number denoting the offset
        of the camera from the cameras' target.

        :returns: The offset
        :rtype: float

        """
        return self._offset

    @offset.setter
    def offset(self, offset):
        """
        Set the offset of the camera from
        the "filmed" target. The offset value
        gets sanitized and converted to float
        if necessary.

        :param offset: Offset value
        :returns: None
        :rtype: None

        """
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
        """
        Get the cameras field of view.

        :returns: The field of view angle
        :rtype: float

        """
        return self._fow

    @fow.setter
    def fow(self, fow):
        """
        Set the field of view. Only has an
        effect when the camera mode is set
        projectively.

        :param fow: Field of view angle
        :returns: None
        :rtype: None

        """
        self._fow = float(fow)

    @property
    def ratio(self):
        """
        Get the viewport ratio.

        :returns: The viewport ratio
        :rtype: tuple

        """
        return self._ratio

    @property
    def asprat(self):
        """
        Get the viewport aspect ratio.

        :returns: The viewport aspect ratio
        :rtype: float

        """
        return self._asprat

    @property
    def ratioref(self):
        """
        Get min(*self.ratio)

        :returns: The smaller viewport edge
        :rtype: number

        """
        return self._ratioref

    @ratio.setter
    def ratio(self, ratio):
        """
        Set the viewport width and height. Also calculates
        asprat and ratioref.

        :param ratio: A (width, height) tuple
        :returns: None
        :rtype: None

        """
        gl.glViewport(0, 0, *ratio)

        self._ratio = ratio
        self._asprat = op.truediv(*ratio)
        self._ratioref = min(ratio)

        self._reinitialize()
        trace('set camera ratio to %s, asprat: %f and ratioref: %d' % (
            self.ratio, self.asprat, self.ratioref))

    @property
    def mode(self):
        """
        Get the current camera mode. The mode is one of
        render.Camera.MODE_ORTHOGONALLY and
        render.Camera.MODE_PROJECTIVE

        :returns: 0 or 1
        :rtype: number

        """
        return self._mode

    @mode.setter
    def mode(self, mode):
        """
        Set the camera mode to render.Camera.MODE_ORTHOGONALLY
        or render.Camera.MODE_PROJECTIVE

        :param mode: 0 or 1
        :returns: None
        :rtype: None

        """
        self._mode = mode
        self._reinitialize()


#
#   SCENE
#
@Singleton
class Scene(object):
    """

    Foremost class is the Scene singleton.
    The main rendering loop is defined therein.
    The scene may be configured by various options
    to alter the appearance of the rendered image.
    The scene maintains a list of entities that
    handle their rendering themselves.

    """

    def __init__(self):
        """
        Initialize the scene singleton.

        :returns: self
        :rtype: render.Scene

        """
        log('initializing scene')
        self._shadow = False
        self._entities = []
        self._lights = []

        log('initializing handler')
        self.evt = Handler(self)

        gl.glEnable(gl.GL_NORMALIZE)
        gl.glEnable(gl.GL_DEPTH_TEST)

    @property
    def shading(self):
        """
        Return the surface shader mode.

        :returns: The shader model
        :rtype: string

        """
        return self._shading

    def setShading(self, value):
        """
        Set the shader model. Accepted values
        are 'flat' and 'smooth'.

        :param value: 'flat' or 'smooth'
        :returns: None
        :rtype: None

        """
        log('setting scene shader to %s' % value)
        gl.glEnable(gl.GL_LIGHTING)

        if value == 'flat':
            gl.glShadeModel(gl.GL_FLAT)

        if value == 'smooth':
            gl.glShadeModel(gl.GL_SMOOTH)

        self._shading = value

    @property
    def repaint(self):
        """
        Repaint callback. Most likely
        glutPostRedisplay

        :returns: The repaint callback function
        :rtype: function

        """
        return self._repaint

    @repaint.setter
    def repaint(self, value):
        """
        Set the repaint callback function.
        Most likely glutPostRedisplay

        :param value: repaint callback
        :returns: None
        :rtype: None

        """
        self._repaint = value

    @property
    def callback(self):
        """
        Return the callback.

        :returns: The callback
        :rtype: function

        """
        return self._callback

    @callback.setter
    def callback(self, value):
        """
        Set the callback. This function
        gets called after every rendering
        cicle. Most likely glutSwapBuffers.

        :param value: Callback function
        :returns: None
        :rtype: None

        """
        self._callback = value

    @property
    def background(self):
        """
        Get the scenes background color

        :returns: A four dimensional point
        :rtype: list

        """
        return self._background

    @background.setter
    def background(self, value):
        """
        Set the scenes background color.

        :param value: A four dimensional point
        :returns: None
        :rtype: None

        """
        self._background = value

    @property
    def camera(self):
        """
        Get the scenes camera.

        :returns: The camera
        :rtype: render.Camera

        """
        return self._camera

    @camera.setter
    def camera(self, cam):
        """
        Set the scenes camera.

        :param cam: The camera
        :returns: None
        :rtype: None

        """
        self._camera = cam

    @property
    def entities(self):
        """
        Return all entities added to the scene.

        :returns: Scene entities
        :rtype: list

        """
        return self._entities

    @property
    def shadow(self):
        """
        Return if the shadow is activated or not.

        :returns: Shadow flag
        :rtype: bool

        """
        return self._shadow

    def toggleShadow(self):
        """
        Either activates or deactivates
        entity shadows.

        :returns: None
        :rtype: None

        """
        self._shadow = False if self.shadow else True

    def addEntity(self, polyhedron):
        """
        Add a geometry to the scene. It gets wrapped into
        a render.Entity. The entities render
        method gets invoked every rendering cicle.

        :param polyhedron: A geometry.* instance
        :returns: Entity that wraps the geometry
        :rtype: render.Entity

        """
        log('adding polyhedron "%s" to scene' % polyhedron)
        ent = Entity(polyhedron)
        ent.mode = gl.GL_LINE if self.shading == 'grid' else gl.GL_FILL
        self._entities.append(ent)
        return ent

    def createLight(self):
        """
        Create and append a light to the scene.

        :returns: The created light
        :rtype: render.Light

        """
        light = Light()
        self._lights.append(light)
        return light

    def render(self):
        """
        Main rendering dispatcher. Invokes the rendering
        of all entities and lights. Also sets the shader model
        etc. according to the properties.

        :returns: None
        :rtype: None

        """
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
            shadow = self._lights[0] if self.shadow else None
            ent.render(self.camera, shadow)

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
