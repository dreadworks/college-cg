#!/usr/bin/env python
# -*- coding: utf-8 -*-


import numpy as np
import operator as op
from OpenGL.arrays import vbo

import logging
log = logging.getLogger('bezier')


class VertexException():

    def __str__(self):
        return 'VertexException: ' + self._msg

    def __init__(self, msg):
        self._msg = msg


class VertexObject(object):

    def _resizeBuffer(self, mathop):
        nsize = mathop(self._bufsize, self._bufstep)
        log.info('resizing buffer from %d to %d', self._bufsize, nsize)
        self._bufsize = nsize

        self._vbo = None
        self._stack.resize((self._bufsize, 3))
        self._vbo = vbo.VBO(self._stack)

    def __init__(self, bufsize):
        self._bufstep = bufsize
        self._bufsize = bufsize
        self._head = 0

        self._stack = np.zeros((bufsize, 3), 'f')
        self._vbo = vbo.VBO(self._stack)

    @property
    def vbo(self):
        return self._vbo

    @vbo.setter
    def vbo(self, value):
        self._vbo = value

    @property
    def size(self):
        return self._head

    @property
    def scale(self):
        return self._scale

    @property
    def offset(self):
        return self._offset

    def add(self, x, y):
        # prevent buffer overflow
        if (self._head + 2 >= self._bufsize):
            self._resizeBuffer(op.add)

        self._stack[self._head] = [x, y, 0]
        self._head += 1

    def undo(self):
        if (self._head - 1 < 0):
            msg = 'The vertex object is already empty'
            raise VertexException(msg)

        self._head -= 1
        threshold = self._bufsize - self._bufstep
        if (self._head < threshold):
            self._resizeBuffer(op.sub)