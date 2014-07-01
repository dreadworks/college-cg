#!/usr/bin/env python
# -*- coding: utf-8 -*-


import numpy as np
import operator as op
from OpenGL.arrays import vbo

from util import LOG
log = LOG.out


class VertexException():

    def __str__(self):
        return self._msg

    def __init__(self, msg):
        self._msg = msg


class VertexObject(object):

    def _add(self, *points):
        self._offset = len(points)

        while (self._head + self._offset >= self._bufsize):
            self._resizeBuffer(op.add)

        for point in points:
            self._stack[self._head] = map(float, point)
            self._head += 1

        self._vbo.set_array(self._stack)

    def _setBuffer(self, size):
        log.info('setting buffer to size %d', size)
        self._bufsize = size

        self._vbo = None
        self._stack.resize((self._bufsize, 2))
        self._vbo = vbo.VBO(self._stack)

    def _resizeBuffer(self, mathop):
        size = mathop(self._bufsize, self._bufstep)
        log.info('resizing buffer from %d to %d', self._bufsize, size)
        self._setBuffer(size)

    def __init__(self, bufsize):
        log.info('initializing vertex object with buffer size %d', bufsize)
        self._bufstep = bufsize
        self._bufsize = bufsize
        self._head = 0

        self._stack = np.zeros((bufsize, 2), 'f')
        self._vbo = vbo.VBO(self._stack)

    @property
    def vbo(self):
        return self._vbo

    @property
    def size(self):
        return self._head

    @property
    def scale(self):
        return self._scale

    @property
    def offset(self):
        return self._offset

    def get(self, amount):
        # combining the slices into one [] behaves
        # somewhat nasty...
        return map(tuple, self._stack[:self.size][::-1][:amount])

    def addPoint(self, x, y):
        log.trace('adding %d, %d to vertex object', x, y)
        self._add([x, y])

    def addPoints(self, *coll):
        log.trace('adding point collection of size %d', len(coll))
        self._add(*coll)

    def undo(self):
        if (self._head - 1 < 0):
            msg = 'The vertex object is already empty'
            raise VertexException(msg)

        msg = 'removing %d points from vertex object'
        log.info(msg, self._offset)

        self._head -= self._offset
        threshold = self._bufsize - self._bufstep
        while (self._head < threshold):
            self._resizeBuffer(op.sub)
            threshold -= self._bufstep

    def empty(self, resizeBuffer=True):
        self._head = 0
        if resizeBuffer:
            self._setBuffer(self._bufstep)
