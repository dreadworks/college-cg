#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from geometry import *


class PointTests(unittest.TestCase):

    def testConstruction(self):
        p = Point((1, 2, 3))
        self.assertTrue(type(p) is Point)
        with self.assertRaises(GeometryException):
            Point(3)

    def testConversion(self):
        t = (1, 2, 3)
        p = Point(t)
        self.assertEqual(t, p.raw)

    def testDimension(self):
        t1 = (1, 2, 3)
        t2 = (1, 2)
        p1 = Point(t1)
        p2 = Point(t2)
        self.assertEqual(p1.dimension, len(t1))
        self.assertEqual(p2.dimension, len(t2))

    def testEquality(self):
        p1 = Point((1, 2, 3))
        p2 = Point((1, 2, 3))
        p3 = Point((0, 1, 2))
        self.assertTrue(p1 == p2)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)

    def testRepr(self):
        p1 = Point((1, 2, 3))
        p2 = eval(repr(p1))
        self.assertEqual(p1, p2)

    def testClone(self):
        p1 = Point((1, 2, 3))
        p2 = p1.clone()
        self.assertEqual(p1, p2)

    def testStr(self):
        p1 = Point((1, 2, 3))
        self.assertEqual(str(p1), "Point: (1.0, 2.0, 3.0)")

    def testSub(self):
        p1 = Point((0, 3, 0))
        p2 = Point((0, 2, 5))
        v = p2 - p1
        self.assertTrue(type(v) is Vector)
        self.assertEqual(v, Vector((0, -1, 5)))

    def testAdd(self):
        p1 = Point((1, 2))
        p2 = Point((2, 3))
        with self.assertRaises(GeometryException):
            p1 + p2


class VectorTests(unittest.TestCase):

    def testConstruction(self):
        v = Vector((1, 2, 3))
        self.assertTrue(type(v) is Vector)
        with self.assertRaises(GeometryException):
            v = Vector(3)

    def testConversion(self):
        t = (1, 2, 3)
        v = Vector(t)
        self.assertEqual(t, v.raw)

    def testDimension(self):
        t1 = (1, 2, 3)
        t2 = (1, 2)
        v1 = Vector(t1)
        v2 = Vector(t2)
        self.assertEqual(v1.dimension, len(t1))
        self.assertEqual(v2.dimension, len(t2))

    def testEquality(self):
        v1 = Vector((1, 2, 3))
        v2 = Vector((1, 2, 3))
        v3 = Vector((0, 1, 2))
        self.assertTrue(v1 == v2)
        self.assertEqual(v1, v2)
        self.assertNotEqual(v1, v3)

    def testRepr(self):
        v1 = Vector((1, 2, 3))
        v2 = eval(repr(v1))
        self.assertEqual(v1, v2)

    def testClone(self):
        v1 = Vector((1, 2, 3))
        v2 = v1.clone()
        self.assertEqual(v1, v2)

    def testStr(self):
        v1 = Vector((1, 2, 3))
        self.assertEqual(str(v1), "Vector: (1.0, 2.0, 3.0)")

    def testInv(self):
        v1 = Vector((1, -1, 5))
        self.assertEqual(-v1, Vector((-1, 1, -5)))

    def testAdd(self):
        v1 = Vector((1, 2, 3))
        v2 = Vector((3, 2, 1))
        self.assertEqual(v1 + v2, Vector((4, 4, 4)))

    def testSub(self):
        v1 = Vector((1, 2, 3))
        v2 = Vector((3, 2, 1))

    def testSMul(self):
        t = (1, 2, 4)
        v1 = Vector(t)
        v2 = Vector(tuple(map(lambda x: x*2, t)))
        self.assertEqual(v1 * 2, v2)
        self.assertEqual(v1.raw, t)

    def testSProd(self):
        t = (1, 2, 4)
        v1 = Vector(t)
        v2 = Vector(t)
        self.assertEqual(v1 * v2, 21)

    def testCProd(self):
        t = (1, 2, 4)
        v1 = Vector(t)
        v2 = Vector(t)
        self.assertEqual(v1 ** v2, Vector((0, 0, 0)))

    def testDiv(self):
        t = (2, 4, 8)
        v1 = Vector(t)
        v2 = Vector(tuple(map(lambda x: x/2, t)))
        self.assertEqual(v1 / 2, v2)
        self.assertEqual(v1.raw, t)

    def testLen(self):
        v1 = Vector((3, 4, 0))
        v2 = Vector((-3, 4, 0))
        self.assertEqual(v1.length, 5.)
        self.assertEqual(v2.length, 5.)

    def testNormalization(self):
        v = Vector((4, 8, 4))
        v = v.normalize()
        self.assertEqual(v.length, 1)

    def testSProdLenEq(self):
        v = Vector((3, -2, 5))
        self.assertAlmostEqual(v*v, v.length**2)

    def testMap(self):
        quad = lambda c: c**2
        t = (-3, 0, 2)
        tq = tuple(map(quad, t))

        v1 = Vector(t)
        v2 = v1.map(quad)

        self.assertEqual(v1, Vector(t))
        self.assertEqual(v2, Vector(tq))

    def testMirror(self):
        s = Sphere(Point((6, 0, 0)), 2)
        r = Ray(Point((0, 0, 0)), Vector((1, 0, 0)))

        p = r.shoot(s.intersection(r))
        l = Point((0, 4, 0)) - p
        n = s.normal(p)
        self.assertEqual(l.mirror(n), Vector((-4, -4, 0)))

        l = Point((0, 0, 0)) - p
        self.assertEqual(l.mirror(n), Vector((-4, 0, 0)))

    def testCombine(self):
        v1 = Vector((1, 2, 3))
        v2 = v1.clone()
        v3 = v1.combine(v2, op.mul)
        self.assertEqual(v3, v1.map(lambda c: c**2))


class OperationTests(unittest.TestCase):

    def testAdd(self):
        v = Vector((1, 2))
        p1 = Point((4, 5))
        p2 = p1 + v
        self.assertTrue(type(p2) is Point)
        self.assertEqual(p2, Point((5, 7)))


class RayTests(unittest.TestCase):

    def setUp(self):
        self.p = Point((1, 2, 3))
        self.v = Vector((1, 0, 0))
        self.r = Ray(self.p, self.v)

    def testConstruction(self):
        self.assertTrue(type(self.r) is Ray)
        with self.assertRaises(GeometryException):
            Ray(1, self.v)
        with self.assertRaises(GeometryException):
            Ray(self.p, 1)

        self.assertEqual(self.r.origin, self.p)
        self.assertEqual(self.r.direction, self.v)

        ray = Ray(self.p.raw, self.v.raw)
        self.assertEqual(ray.origin, self.p)
        self.assertEqual(ray.direction, self.v)

    def testEquality(self):
        r2 = Ray(self.p, self.v)
        r3 = Ray(self.p, Vector((5, 4, 3)))
        r4 = Ray(Point((23, 24, 23)), self.v)

        self.assertTrue(self.r == r2)
        self.assertEqual(self.r, r2)
        self.assertNotEqual(self.r, r3)
        self.assertNotEqual(self.r, r4)

    def testRepr(self):
        r2 = eval(repr(self.r))
        self.assertEqual(self.r, r2)

    def testClone(self):
        r2 = self.r.clone()
        self.assertEqual(self.r, r2)

    def testStr(self):
        s = "Ray: (%s, %s)" % (str(self.p), str(self.v))
        self.assertEqual(str(self.r), s)

    def testShoot(self):
        v = self.r.shoot(20)
        self.assertEqual(v, Point((21, 2, 3)))


class SphereTests(unittest.TestCase):

    def setUp(self):
        self.rp = Point((0, 0, 0))
        self.rv = Vector((1, 0, 0))
        self.r = Ray(self.rp, self.rv)

        self.scnt = Point((6, 0, 0))
        self.srad = 2
        self.s = Sphere(self.scnt, self.srad)

        self.srad = float(self.srad)

    def testConstruction(self):
        self.assertTrue(type(self.s) is Sphere)
        with self.assertRaises(GeometryException):
            Sphere(self.scnt, (1,))
        with self.assertRaises(GeometryException):
            Sphere(1, self.srad)

        self.assertEqual(self.s.center, self.scnt)
        self.assertEqual(self.s.radius, self.srad)

    def testEquality(self):
        s = Sphere(self.scnt, self.srad)
        self.assertTrue(self.s == s)
        self.assertEqual(self.s, s)

        s = Sphere(self.scnt, 5)
        self.assertNotEqual(self.s, s)

        s = Sphere(Point((0, 0, 0)), self.srad)
        self.assertNotEqual(self.s, s)

    def testRepr(self):
        s2 = eval(repr(self.s))
        self.assertEqual(self.s, s2)

    def testClone(self):
        s2 = self.s.clone()
        self.assertEqual(self.s, s2)

    def testStr(self):
        s = "Sphere: (%s, %s)" % (str(self.scnt), str(self.srad))
        self.assertEqual(str(self.s), s)

    def testNormal(self):
        p = Point((2, 0, 0))
        n = self.s.normal(p)
        self.assertEqual(n, -self.rv.normalize())

    def testIntersection(self):
        i = self.r.shoot(self.s.intersection(self.r))
        self.assertEqual(i, Point((4, 0, 0)))

        self.r.direction = -self.rv
        p = self.r.shoot(self.s.intersection(self.r))
        self.assertEqual(p, Point((8, 0, 0)))

        self.r.direction = Vector((1, 1, 0))
        self.assertIsNone(self.s.intersection(self.r))


class PlaneTests(unittest.TestCase):

    def setUp(self):
        self.rp = Point((0, 0, 0))
        self.rv = Vector((1, 0, 0))
        self.r = Ray(self.rp, self.rv)

        self.pp = Point((2, 0, 0))
        self.pn = Vector((1, 0, 0))
        self.p = Plane(self.pp, self.pn)

    def testConstruction(self):
        self.assertTrue(type(self.p) is Plane)
        with self.assertRaises(GeometryException):
            Plane(self.pp, (1,))
        with self.assertRaises(GeometryException):
            Sphere(1, self.pn)

        self.assertEqual(self.p.point, self.pp)
        self.assertEqual(self.p.norm, self.pn)

    def testEquality(self):
        p = Plane(self.pp, self.pn)
        self.assertTrue(self.p == p)
        self.assertEqual(self.p, p)

        # TODO @see geometry.Plane.__eq__
        # p = Plane(self.pp, Vector((-1, 0, 0)))
        # self.assertEqual(self.p, p)
        # p = Plane(Point((2, 3, 0)), self.pn)
        # self.assertEqual(self.p, p)

        p = Plane(self.pp, Vector((1, 1, 0)))
        self.assertNotEqual(self.p, p)

        p = Plane(Point((0, 0, 0)), self.pn)
        self.assertNotEqual(self.p, p)

    def testRepr(self):
        p = eval(repr(self.p))
        self.assertEqual(self.p, p)

    def testClone(self):
        p = self.p.clone()
        self.assertEqual(self.p, p)

    def testStr(self):
        s = "Plane: (%s, %s)" % (str(self.pp), str(self.pn))
        self.assertEqual(str(self.p), s)

    def testNormal(self):
        p = Point((2, 0, 0))
        n = self.p.normal(p)
        self.assertEqual(n, self.p.norm)

    def testIntersection(self):
        i = self.r.shoot(self.p.intersection(self.r))
        self.assertEqual(i, Point((2, 0, 0)))

        self.r.direction = Vector((1, 1, 0))
        i = self.r.shoot(self.p.intersection(self.r))
        self.assertEqual(i, Point((2, 2, 0)))

        self.r.direction = Vector((0, 1, 0))
        self.assertIsNone(self.p.intersection(self.r))


class TriangleTests(unittest.TestCase):

    def setUp(self):
        self.rp = Point((0, 0, 0))
        self.rv = Vector((1, 0, 0))
        self.r = Ray(self.rp, self.rv)

        vertices = [(2, 1, 0), (2, -1, -1), (2, -1, 1)]
        self.vertices = tuple(map(Point, vertices))
        self.t = Triangle(*self.vertices)

    def testConstruction(self):
        self.assertTrue(type(self.t) is Triangle)
        with self.assertRaises(GeometryException):
            Triangle(1, 2, 3)

        self.assertEqual(self.t.vertices, self.vertices)

    def testEquality(self):
        t = Triangle(*self.vertices)
        self.assertTrue(self.t == t)
        self.assertEqual(self.t, t)

        vertices = [(10, 20, 30), (11, 21, 31), (0, 0, 0)]
        vertices = tuple(map(Point, vertices))
        t = Triangle(*vertices)
        self.assertNotEqual(self.t, t)

    def testRepr(self):
        t = eval(repr(self.t))
        self.assertEqual(self.t, t)

    def testClone(self):
        t = self.t.clone()
        self.assertEqual(self.t, t)

    def testStr(self):
        s = "Triangle: (%s, %s, %s)" % tuple(map(str, self.vertices))
        self.assertEqual(str(self.t), s)

    def testNormal(self):
        n = self.t.normal(Point((2, 0, 0)))
        self.assertEqual(n, Vector((-1, 0, 0)))

    def testIntersection(self):
        i = self.r.shoot(self.t.intersection(self.r))
        self.assertEqual(i, Point((2, 0, 0)))

        self.r.direction = Vector((0, 1, 0))
        self.assertIsNone(self.t.intersection(self.r))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
