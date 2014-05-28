#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

import geometry as gm
import bodies as bd

from raytracer import *


class WorldTests(unittest.TestCase):

    def setUp(self):
        self.world = World((1, 0, 0))
        self.world.lightness = 0.5

        self.raw_bodies = (
            bd.Sphere((0, 10, 0), 1),
            bd.Sphere((5, 0, 0), 1),
            bd.Sphere((2, 0, 0), 1)
        )

        self.world.addBodies(*self.raw_bodies)
        self.hitray = gm.Ray((0, 0, 0), (1, 0, 0))
        self.disray = gm.Ray((0, 0, 0), (0, 1, 0))
        self.misray = gm.Ray((0, 0, 0), (-1, 0, 0))

    def testSimpleTrace(self):
        o, p = self.world.trace(self.misray)
        self.assertIsNone(o)
        self.assertIsNone(p)

        # test that it finds the "first" sphere
        o, p = self.world.trace(self.hitray)
        self.assertEqual(o, self.raw_bodies[2])
        self.assertEqual(p, gm.Point((1, 0, 0)))

    def testMaxdistTrace(self):
        o, p = self.world.trace(self.disray)
        self.assertEqual(o, self.raw_bodies[0])
        self.assertEqual(p, gm.Point((0, 9, 0)))

        o, p = self.world.trace(self.disray, maxdist=5)
        self.assertIsNone(o)
        self.assertIsNone(p)
