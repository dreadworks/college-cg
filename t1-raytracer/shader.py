#!/usr/bin/env python
# -*- coding: utf-8 -*-


import math
import operator as op
import geometry as gm


class Phong(object):
    """
    Phong shader. Determines a pixels color value.
    """

    def __str__(self):
        return "Phong Shader with recursion depth %d" % self.depth

    def __init__(self, world, depth):
        self._world = world
        self._depth = depth

    @property
    def world(self):
        return self._world

    @property
    def depth(self):
        return self._depth

    def diffus(self, obj, cosphi):
        """
        Calculates the diffus factor of the phong
        shading based on the objects shininess/smoothness
        and the cosine of the normal with the lights ray.

        obj    -- Body touched by the light
        cosphi -- Dot product of the bodies normal and the light
        """
        factor = (1 - obj.shininess) * cosphi
        # abs(factor) would work as if the light
        # is mirrored on the other side of the object
        factor = 0 if factor < 0 else factor
        return factor

    def specular(self, obj, cosphi, costheta):
        """
        Calculates the specular factor of the phong shading.
        It is based on the objects reflectiveness.

        obj      -- Reflective body
        cosphi   -- Dot product of the bodies normal and the light
        costheta -- Dot product the view ray and the reflected light ray
        """
        if costheta > 0:
            factor = (obj.smoothness + 2) / (2 * math.pi)
            factor *= costheta ** obj.smoothness
            factor *= obj.shininess
            return factor
        return 0

    def colorize(self, ray, d):
        """
        Handles the n'th recursive colorization step.
        Checks for intersections with the worlds bodies
        and determines a color value based on the bodies
        properties.

        ray -- geometry.Ray instance
        d   -- Recursion step. Aborts at 0
        """
        obj, point = self.world.trace(ray, maxdist=self.world.maxdist)
        if obj is None:
            return self.world.background

        normal = obj.geometry.normal(point)

        # ambient
        color = obj.colorAt(point) * self.world.lightness
        # color = gm.Vector((0, 0, 0))

        #
        #   exercise shading for every light source
        #
        for light in self.world.lights:
            lightvec = (light.geometry - point).normalize()
            lightray = gm.Ray(point, lightvec)

            collection = self.world.bodies.difference((obj,))
            hit, p = self.world.trace(lightray, collection)
            if hit is not None:
                continue

            # intensify the objects color
            # based on the lights components
            # instead of just adding up
            lightc = obj.colorAt(point).combine(light.color / 0xff, op.mul)

            # diffus
            cosphi = (normal * lightvec)
            factor = self.diffus(obj, cosphi)
            color += lightc * factor

            # specular
            costheta = -ray.direction * lightvec.mirror(normal)
            factor = self.specular(obj, cosphi, costheta)
            color += light.color * factor

        # recursive reflection handling
        if d > 0:
            factor = obj.shininess
            direction = -(ray.direction).mirror(normal)
            ray = gm.Ray(point, direction)
            color += self.colorize(ray, d - 1) * factor

        # refraction (TODO)
        # ...
        return color

    def shade(self, ray):
        """
        The shaders main entry point. Starts colorization
        and returns a normalized color tuple.

        ray -- A geometry.Ray instance
        """
        color = self.colorize(ray, self.depth)
        factor = max(color.raw) / float(0xff)
        if factor > 1:
            color /= factor

        return tuple(map(int, color.raw))
