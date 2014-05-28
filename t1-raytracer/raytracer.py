#!/usr/bin/env python
# -*- coding: utf-8 -*-


import math
import json

from PIL import Image

import geometry as gm
import bodies as bd
from shader import Phong as Shader


#
#   CONSTANTS
#

VERBOSE = False
EMSG = {
    'setter': '%s: Expected %s, got %s'
}


#
#   EXCEPTIONS
#


class RaytraceException(Exception):

    def __str__(self):
        return self.msg

    def __init__(self, msg):
        self.msg = msg


#
#   RAYTRACER
#


class Raytracer(object):
    """
    Base class with shared methods for convenience.
    """

    def _throw(self, fmt, *args):
        msg = EMSG[fmt] % tuple(args)
        raise RaytraceException(msg)

    def _typecheck(self, name, arg, argtype):
        if (type(arg) is not argtype):
            self._throw('setter', name, argtype, type(arg))

    def _instancecheck(self, name, instance, *bases):
        if not isinstance(instance, tuple(bases)):
            self._throw('setter', name, str(bases), str(instance))


class World(Raytracer):
    """
    World instances describe the scenes to take pictures from.
    They hold the collections of all entities (lights, bodies...)
    and the center for the camera. Some other environmental attributes
    are maintained by this class, too.
    """

    def __init__(self, center):
        self.center = center
        self._bodies = set()
        self._lights = []

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, color):
        self._typecheck("World.background", color, tuple)
        self._background = gm.Vector(color)

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, cntr):
        self._typecheck("World.center", cntr, tuple)
        self._center = gm.Point(cntr)

    @property
    def maxdist(self):
        return self._maxdist

    @maxdist.setter
    def maxdist(self, maxdist):
        self._instancecheck("World.maxdist", maxdist, (int, float))
        self._maxdist = maxdist

    @property
    def bodies(self):
        return self._bodies

    def addBodies(self, *objs):
        for obj in objs:
            self._instancecheck('World.addBodies', obj, bd.Body)
        self._bodies.update(objs)

    @property
    def lightness(self):
        return self._lightness

    @lightness.setter
    def lightness(self, lightness):
        self._typecheck('World.lightness', lightness, float)
        self._lightness = lightness

    @property
    def lights(self):
        return self._lights

    def addLight(self, light):
        self._instancecheck('World.addLight', light, bd.Light)
        self._lights.append(light)

    def trace(self, ray, collection=None, maxdist='inf'):
        """
        Takes a ray and checks if there are any bodies
        touched by that ray. Returns the nearest body
        in range.

        ray        -- A geometry.Ray instance
        collection -- (Optional) Which collection to check
                      for intersections. Defaults to the
                      worlds body collection.
        maxdist    -- (Optional) Everything out of this
                      range is not considered a match.
        """
        maxdist = float(maxdist)
        if collection is None:
            collection = self.bodies

        obj, minhit = None, None
        for elem in collection:
            hit = elem.geometry.intersection(ray)
            if hit and 1e-5 <= hit and hit < maxdist:
                if not minhit or hit < minhit:
                    obj, minhit = elem, hit

        if minhit is not None:
            return obj, ray.shoot(minhit)
        return (None, None)


class Camera(Raytracer):

    def __init__(self, world, res, fow):
        """
        Camera constructor.

        world -- A raytracer.World instance
        res   -- A tuple describing the desired resolution
        fow   -- The Cameras field of view (45-60 is good)
        """
        self.world = world
        self._res = res

        alpha = fow / 2.
        self._height = 2 * math.tan(alpha)

        asprat = self.reswidth / float(self.resheight)
        self._width = asprat * float(self.height)

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, world):
        self._typecheck('Camera.world', world, World)
        self._world = world

    @property
    def shader(self):
        return self._shader

    @shader.setter
    def shader(self, shader):
        self._shader = shader

    @property
    def resolution(self):
        return self._res

    @property
    def reswidth(self):
        return self._res[0]

    @property
    def resheight(self):
        return self._res[1]

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def sys(self, eye, up):
        """
        Creates the camera coordinate system
        to emulate a camera sensor.

        eye -- Point to look from
        up  -- The cameras tilt
        """
        self._typecheck('Camera.shoot (eye)', eye, gm.Point)
        self._typecheck('Camera.shoot (up)', up, gm.Vector)

        # build coordinate system
        f = (self.world.center - eye).normalize()
        s = (f ** up).normalize()
        u = s ** f

        return f, s, u

    def sweep(self, f, s, u, eye):
        """
        Generator that yields for
        every pixel in the image matrix
        the corresponding x, y values and
        a ray instance.

        f, s, u -- Camera parameters (@see self.sys)
        eye     -- Point to look from
        """
        pw = self.width / (self.reswidth - 1)
        ph = self.height / (self.resheight - 1)

        for x in range(self.reswidth):
            for y in range(self.resheight):
                xcmp = s * (x * pw - self.width / 2)
                ycmp = u * (y * ph - self.height / 2)
                yield x, y, gm.Ray(eye, f + xcmp + ycmp)

    def shoot(self, eye, up, img):
        """
        Takes the necessary camera parameters
        and an PIL Image instance to shoot
        a picture from the world.

        eye -- Point to look from
        up  -- The cameras tilt
        img -- An PIL Image instance
        """
        eye = gm.Point(eye)
        up = -gm.Vector(up)

        args = self.sys(eye, up)
        args += (eye,)

        for x, y, ray in self.sweep(*args):
            color = self.shader.shade(ray)
            img.putpixel((x, y), color)


#
#   UTILITY
#


def log(msg):
    if VERBOSE:
        print(msg)


class Importer(object):
    """
    Reads a json file and translates its configuration
    to an environment for shooting raytraced pictures.
    """

    def _readcolor(self, cstr):
        """
        Accepts a string consisting of
        three hexadecimal rgb color values
        and returns a tuple of three integers.

        cstr -- Valuestring of format [\da-fA-F]{6}
        """
        step = 2
        l = [cstr[i:i + step] for i in range(0, len(cstr), 2)]
        l = map(lambda s: int(s, 16), l)
        return tuple(l)

    def _importTCheckerboard(self, raw):
        colors = map(self._readcolor, raw['colors'])
        return bd.CheckerboardTexture(raw['size'], tuple(colors))

    def _setMaterial(self, body, raw):
        """
        Meta function for all bodies sharing
        the same properties.

        body -- bodies.Body instance
        raw  -- json configuration
        """
        if 'texture' in raw:
            handler = raw['texture']['type']
            handler = self._texturehandler[handler]
            body.texture = handler(raw['texture'])
        else:
            body.color = self._readcolor(raw['color'])

        body.shininess = raw['shininess']
        body.smoothness = raw['smoothness']

    def _importSphere(self, raw):
        """
        Sphere factory.

        raw -- json configuration
        """
        position = tuple(raw['position'])
        sphere = bd.Sphere(position, raw['radius'])
        return sphere

    def _importPlane(self, raw):
        """
        Plane factory.

        raw -- json configuration
        """
        point = tuple(raw['point'])
        norm = tuple(raw['norm'])
        plane = bd.Plane(point, norm)
        return plane

    def _importTriangle(self, raw):
        """
        Triangle factory.

        raw -- json configuration
        """
        a, b, c = tuple(map(tuple, raw['vertices']))
        triangle = bd.Triangle(a, b, c)
        return triangle

    def __init__(self, fname):
        """
        Create an instance of the importer.

        fname -- file name of the json configuration
        """
        with open(fname) as f:
            self.json = json.load(f)

        self._world = None
        self._camera = None

        # ...there must be a nicer way
        self._bodyhandler = {
            'sphere': self._importSphere,
            'plane': self._importPlane,
            'triangle': self._importTriangle
        }

        self._texturehandler = {
            'checkerboard': self._importTCheckerboard
        }

    @property
    def world(self):
        """
        Returns a World instance.
        """
        if self._world is None:
            raw = self.json['world']
            world = World(tuple(raw['center']))
            world.lightness = raw['lightness']
            world.background = self._readcolor(raw['background'])
            world.maxdist = raw['maxdist']
            self._world = world
        return self._world

    @property
    def camera(self):
        """
        Returns the camera object needed to
        shoot pictures.
        """
        if self._camera is None:
            raw = self.json['camera']
            res = tuple(raw['resolution'])
            aow = raw['angleofview']
            self._camera = Camera(self.world, res, aow)
        return self._camera

    @property
    def positions(self):
        """
        Describes the positions in the world
        from where pictures are getting taken.
        Yields tuples of the "eye"-point and
        up-vector necessary for the camera.
        """
        for raw in self.json['pictures']:
            eye = tuple(raw['eye'])
            up = tuple(raw['up'])
            yield (eye, up)

    @property
    def recdepth(self):
        """
        The shaders recursion depth. Describes
        how often the view ray "bounces" between
        reflective bodies.
        """
        return self.json['recdepth']

    def bodies(self):
        """
        Adds all defined bodies to the worlds
        object collection. Returns the number
        of imported bodies.
        """
        for raw in self.json['bodies']:
            handler = self._bodyhandler[raw['type']]
            body = handler(raw)
            self._setMaterial(body, raw)
            self.world.addBodies(body)
        return len(self.json['bodies'])

    def lights(self):
        """
        Adds all defined lights to the worlds
        object collection. Returns the number
        of imported lights.
        """
        for raw in self.json['lights']:
            position = tuple(raw['position'])
            light = bd.Light(position)
            light.color = self._readcolor(raw['color'])
            light.lightness = raw['lightness']
            self.world.addLight(light)
        return len(self.json['lights'])

    def done(self):
        """
        Removes the raw json data from memory.
        """
        self.json = None


#
#   MAIN
#
def raytrace(name):
    """
    Generator that yields rendered images.

    name -- File name of a configuration written in json
            relative to where the script is executed.
    """
    imp = Importer(name)

    # import world
    world = imp.world
    log('created world')

    # import entities
    log('imported %d bodies' % imp.bodies())
    log('imported %d lightsources' % imp.lights())

    camera = imp.camera
    camera.shader = Shader(world, imp.recdepth)
    positions = [pos for pos in imp.positions]

    log('imported camera and %d positions' % len(positions))
    log('using %s' % camera.shader)

    imp.done()
    log('free\'d import memory')

    count = 1
    # shoot pictures
    for eye, up in positions:
        log("shooting picture %d/%d" % (count, len(positions)))
        img = Image.new('RGB', camera.resolution)
        camera.shoot(eye, up, img)
        yield img
        count += 1

    log('done')


def main():
    global VERBOSE
    VERBOSE = True

    import sys
    if len(sys.argv) < 2:
        print('Usage: raytracer.py file.json')
        sys.exit(2)

    for img in raytrace(sys.argv[1]):
        img.show()


if __name__ == '__main__':
    main()
