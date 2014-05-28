#!/usr/bin/env python
# -*- coding: utf-8 -*-


import math
import operator as op


EMSG = {
    "point_init":     "Wrong initialization argument: %s.",
    "point_sub":      "Could not subtract points.",
    "point_add":      "Addtion is not defined for Point and %s",
    "vector_prod":    "The cross product is only defined for vectors in R3.",
    "body_overwrite": "The %s method must be overwritten.",
    "setter":         "%s: Wrong argument got provided, expected %s, got %s."
}


class GeometryException(Exception):

    def __str__(self):
        return self.msg

    def __init__(self, msg):
        self.msg = msg


class Point(object):

    def _compwise(self, other, fn):
        try:
            intermed = zip(self.raw, other)
        except TypeError:
            intermed = map(lambda v: (v,), self.raw)

        intermed = map(lambda t: fn(*t), intermed)
        intermed = tuple(intermed)
        return intermed

    def __eq__(self, other):
        try:
            assert(type(self) is type(other))
            return self.raw == other.raw
        except:
            pass
        return False

    def __repr__(self):
        return "%s(%s)" % ("Point", self.raw)

    def __str__(self):
        return "Point: %s" % str(self.raw)

    def __add__(self, v):
        if type(v) is Vector and self.dimension == v.dimension:
            return Point(self._compwise(v.raw, op.add))
        raise GeometryException(EMSG['point_add'] % type(v))

    def __sub__(self, p):
        if self.dimension == p.dimension:
            return Vector(self._compwise(p.raw, op.sub))
        raise GeometryException(EMSG['point_sub'])

    def __init__(self, p):
        if type(p) is tuple:
            self._raw = tuple(map(float, p))
            return

        msg = EMSG['point_init'] % type(p)
        raise GeometryException(msg)

    @property
    def raw(self):
        return self._raw

    @property
    def dimension(self):
        return len(self._raw)

    def clone(self):
        """
        Returns a new Point with the same properties.
        """
        return Point(self.raw)


class Vector(Point):

    def __repr__(self):
        return "%s(%s)" % ("Vector", self.raw)

    def __str__(self):
        return "Vector: %s" % str(self.raw)

    def __neg__(self):
        """
        Invert the vector.
        """
        op = lambda t: -1 * t
        return Vector(self._compwise(None, op))

    def __add__(self, v):
        """
        Add one vector to another.

        v - Another geometry.Vector instance
        """
        return Vector(self._compwise(v.raw, op.add))

    def __sub__(self, v):
        """
        Subtract one vector from another.

        v -- Another geometry.Vector instance
        """
        return Vector(self._compwise(v.raw, op.sub))

    def __div__(self, s):
        """
        Scales the vector.

        s -- Scale factor as scalar value
        """
        v = [s for x in range(self.dimension)]
        return Vector(self._compwise(tuple(v), op.truediv))

    def __mul__(self, e):
        """
        Either scales the vector if e is a scalar
        otherwise calculates the dot product if e
        is a vector.

        e -- Either a vector or scalar
        """
        if (type(e) == type(self)):
            t = self._compwise(e.raw, op.mul)
            return sum(t)
        else:
            v = [e for x in range(self.dimension)]
            return Vector(self._compwise(tuple(v), op.mul))

    def __pow__(self, v):
        """
        Determines the cross product.

        v -- Another geometry.Vector instance
        """
        if self.dimension != 3:
            raise GeometryException(EMSG['vector_prod'])

        flatten = lambda l: [c for t in l for c in t]

        l1 = list(zip(self.raw, v.raw))
        l2 = list(zip(v.raw, self.raw))

        l1 = flatten(l1[1:] + l1[:1])
        l2 = flatten(l2[2:] + l2[:2])

        w = list(map(lambda t: op.mul(*t), zip(l1, l2)))
        w = map(lambda t: op.sub(*t), list(zip(w, w[1:]))[::2])
        return Vector(tuple(w))

    def __init__(self, v):
        super(Vector, self).__init__(v)

    @property
    def length(self):
        length = 0
        for x in self.raw:
            length += math.pow(x, 2)
        return math.sqrt(length)

    def normalize(self):
        """
        Returns a vector with length 1.
        """
        return self / self.length

    def clone(self):
        """
        Returns a new vector with the same properties.
        """
        return Vector(self.raw)

    def map(self, fn):
        """
        Apply the function fn to every
        component of the vector.
        """
        t = map(fn, self.raw)
        return Vector(tuple(t))

    def mirror(self, axis):
        """
        Mirror the vector on an axis. Both vectors
        must face the same direction (have an angle < 90
        with respect to each other). Used for reflection.

        axis -- Mostly the normal of a body
        """
        f = 2 * (self * axis)
        axis *= f
        return -(self - axis)

    def combine(self, v, fn):
        """
        Function that combines two vectors component
        wise with an arbitrary function.

        v  -- Another Vector instance
        fn -- Function that awaits two parameters
        """
        med = zip(self.raw, v.raw)
        med = map(lambda t: fn(*t), med)
        return Vector(tuple(med))


class Ray(object):
    """
    Ray
    """

    def __eq__(self, other):
        try:
            assert(type(self) is type(other))
            c1 = self.origin == other.origin
            c2 = self.direction == other.direction
            return c1 and c2
        except:
            pass
        return False

    def __repr__(self):
        params = (repr(self.origin), repr(self.direction))
        return "Ray(%s, %s)" % tuple(params)

    def __str__(self):
        params = map(str, [self.origin, self.direction])
        return "Ray: (%s, %s)" % tuple(params)

    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, origin):
        if type(origin) is tuple:
            origin = Point(origin)

        if (type(origin) is Point):
            self._origin = origin
        else:
            msg = EMSG['setter'] % ("Ray", type(Point), type(origin))
            raise GeometryException(msg)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        if type(direction) is tuple:
            direction = Vector(direction)

        if (type(direction) is Vector):
            self._direction = direction.normalize()
        else:
            msg = EMSG['setter'] % ("Ray", type(Vector), type(direction))
            raise GeometryException(msg)

    def shoot(self, t):
        """
        Get the Point the ray points to when
        scaled by t.

        t -- Scale factor
        """
        return self.origin + self.direction * t

    def clone(self):
        return Ray(self.origin.clone(), self.direction.clone())


class Body(object):
    """
    Base class for all renderable entities.
    """
    def intersection(self, ray):
        """
        Returns the parameter to which the ray
        can be scaled to reach the first intersection
        with a Body. Returns None if no intersection
        was found.

        ray -- A geometry.Ray instance
        """
        msg = EMSG['body_overwrite'] % 'intersection'
        raise GeometryException(msg)

    def normal(self, point):
        """
        Returns the normal of the body at the
        given point.
        """
        msg = EMSG['body_overwrite'] % 'normal'
        raise GeometryException(msg)


class Sphere(Body):

    def __eq__(self, other):
        try:
            assert(type(self) is type(other))
            c1 = self.center == other.center
            c2 = self.radius == other.radius
            return c1 and c2
        except:
            pass
        return False

    def __repr__(self):
        params = map(repr, [self.center, self.radius])
        return "Sphere(%s, %s)" % tuple(params)

    def __str__(self):
        params = map(str, [self.center, self.radius])
        return "Sphere: (%s, %s)" % tuple(params)

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, c):
        if (type(c) is Point):
            self._center = c
        else:
            msg = EMSG['setter'] % ("Sphere", type(Point), type(c))
            raise GeometryException(msg)

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, r):
        if (isinstance(r, (int, float))):
            self._radius = float(r)
        else:
            msg = EMSG['setter'] % ("Sphere", "numeric", type(r))
            raise GeometryException(msg)

    def normal(self, p):
        return (p - self.center).normalize()

    def intersection(self, ray):
        co = self.center - ray.origin
        f = co * ray.direction
        disc = f ** 2 - co * co + self.radius ** 2
        if disc >= 0:
            return f - math.sqrt(disc)

    def clone(self):
        return Sphere(self.center.clone(), self.radius)


class Plane(Body):

    def __eq__(self, other):
        try:
            assert(type(self) is type(other))

            # TODO
            # 1. check if the normal vectors
            #    are linearly independent
            # 2. check if the point of the one
            #    plane lies inside the other
            # Dependency: Gaussian eliminiation algorithm...

            c1 = self.point == other.point
            c2 = self.norm == other.norm
            return c1 and c2
        except:
            pass
        return False

    def __repr__(self):
        params = map(repr, [self.point, self.norm])
        return "Plane(%s, %s)" % tuple(params)

    def __str__(self):
        params = map(str, [self.point, self.norm])
        return "Plane: (%s, %s)" % tuple(params)

    def __init__(self, point, norm):
        self.point = point
        self.norm = norm

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, c):
        if (type(c) is Point):
            self._point = c
        else:
            msg = EMSG['setter'] % ("Plane", type(Point), type(c))
            raise GeometryException(msg)

    @property
    def norm(self):
        return self._norm

    @norm.setter
    def norm(self, n):
        if (type(n) is Vector):
            self._norm = n.normalize()
        else:
            msg = EMSG['setter'] % ("Plane", type(Vector), type(n))
            raise GeometryException(msg)

    def normal(self, p):
        return self.norm

    def intersection(self, ray):
        cosalpha = ray.direction * self.norm
        if cosalpha:
            op = ray.origin - self.point
            return -(op * self.norm) / cosalpha

    def clone(self):
        return Plane(self.point.clone(), self.norm.clone())


class Triangle(Body):

    def __eq__(self, other):
        try:
            # TODO real equality check where
            #      the order of vertices is
            #      not relevant
            assert(type(self) is type(other))
            for pself, pother in zip(self.vertices, other.vertices):
                assert(pself == pother)
            return True
        except:
            pass
        return False

    def __repr__(self):
        params = map(repr, self.vertices)
        return "Triangle(%s, %s, %s)" % tuple(params)

    def __str__(self):
        params = map(str, self.vertices)
        return "Triangle: (%s, %s, %s)" % tuple(params)

    def __init__(self, a, b, c):
        self.vertices = (a, b, c)
        self.u = b - a
        self.v = c - a

    @property
    def vertices(self):
        return self._vertices

    @vertices.setter
    def vertices(self, t):
        if (type(t) is tuple):
            if len(t) != 3:
                msg = "Triangle vertices count"
                msg = EMSG['setter'] % (msg, 3, len(t))
                raise GeometryException(msg)

            for e in t:
                if not type(e) is Point:
                    fmt = ("Triangle vertex", type(Point), type(e))
                    msg = EMSG['setter'] % fmt
                    raise GeometryException(msg)

            self._vertices = t
            self.a, self.b, self.c = t

        else:
            msg = EMSG['setter'] % ("Triangle", type(tuple), type(t))
            raise GeometryException(msg)

    def normal(self, p):
        return (self.u ** self.v).normalize()

    def intersection(self, ray):
        w = ray.origin - self.a
        dv = ray.direction ** self.v
        cosalpha = dv * self.u

        if cosalpha == 0:
            return None

        wu = w ** self.u
        r = (dv * w) / cosalpha
        s = (wu * ray.direction) / cosalpha

        if 0 <= r and r <= 1 and 0 <= s and s <= 1 and r + s <= 1:
            return (wu * self.v) / cosalpha

    def clone(self):
        return Triangle(*self.vertices)
