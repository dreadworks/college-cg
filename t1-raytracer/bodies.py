#!/usr/bin/env python
# -*- coding: utf-8 -*-


import geometry as gm


class Body(object):
    """
    Base class for all entities of a renderable world.

    The geometry property describes one of the
    geometries defined in geometry.py. The geometry
    must implement a method "intersection".
    """

    def __init__(self, geometry):
        self._texture = None
        self._geometry = geometry

    @property
    def geometry(self):
        return self._geometry

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, ct):
        self._color = gm.Vector(ct)

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, texture):
        self._texture = texture

    def colorAt(self, point):
        if self._texture:
            return self.texture.colorAt(point)
        return self.color


class Light(Body):
    """
    A light source (for the phong shader) is
    simply a point emitting light with an intensity
    value and a color.
    """
    def __init__(self, p):
        geometry = gm.Point(p)
        super(Light, self).__init__(geometry)

    @property
    def lightness(self):
        return self._lightness

    @lightness.setter
    def lightness(self, lightness):
        self._lightness = lightness


class Material(Body):
    """
    Base class for all entities that get intersected
    by rays. It holds the minimum of shared properties
    of these entities.
    """

    def __init__(self, geometry):
        super(Material, self).__init__(geometry)

    @property
    def shininess(self):
        return self._shininess

    @shininess.setter
    def shininess(self, shininess):
        self._shininess = shininess

    @property
    def smoothness(self):
        return self._smoothness

    @smoothness.setter
    def smoothness(self, smoothness):
        self._smoothness = smoothness


class Sphere(Material):

    def __init__(self, pos, radius):
        pos = gm.Point(pos)
        geometry = gm.Sphere(pos, radius)
        super(Sphere, self).__init__(geometry)


class Plane(Material):

    def __init__(self, point, normal):
        point = gm.Point(point)
        normal = gm.Vector(normal)
        geometry = gm.Plane(point, normal)
        super(Plane, self).__init__(geometry)


class Triangle(Material):

    def __init__(self, *vertices):
        vertices = tuple(map(gm.Point, vertices))
        geometry = gm.Triangle(*vertices)
        super(Triangle, self).__init__(geometry)


class CheckerboardTexture(object):

    def __init__(self, checksize, colors):
        self._checksize = checksize
        colors = tuple(map(gm.Vector, colors))
        self._clr1, self._clr2 = colors

    @property
    def checksize(self):
        return self._checksize

    @property
    def color1(self):
        return self._clr1

    @property
    def color2(self):
        return self._clr2

    def colorAt(self, point):
        v = gm.Vector(point.raw)
        v *= (1.0 / self.checksize)
        v = v.map(lambda c: int(abs(c) + 0.5))

        if (v.raw[0] + v.raw[1] + v.raw[2]) % 2:
            return self.color2
        return self.color1
