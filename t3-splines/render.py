#!/usr/bin/env python
# -*- coding: utf-8 -*-

import vertex

import numpy as np
import OpenGL.GL as gl
import OpenGL.GL.shaders as sh

from util import LOG
log = LOG.out


class RenderException(Exception):

    def __str__(self):
        return self._msg

    def __init__(self, msg):
        self._msg = msg


class Shader(object):

    def _getPointer(self, name, cache, getter):
        cache = self._cache[cache]
        if not name in cache:
            pointer = getter(self.program, name)
            cache[name] = pointer
        else:
            pointer = cache[name]
        return pointer

    def _getUniformPointer(self, name):
        return self._getPointer(name, 'uniform', gl.glGetUniformLocation)

    def __init__(self):
        self._cache = {
            'uniform': {},
            'attribute': {}
        }

    @property
    def vertex(self):
        return self._vertex

    @vertex.setter
    def vertex(self, value):
        self._vertex = value, sh.GL_VERTEX_SHADER

    # @property
    # def geometry(self):
    #     return self._geometry

    # @geometry.setter
    # def geometry(self, value):
    #     self._geometry = value

    @property
    def fragment(self):
        return self._fragment

    @fragment.setter
    def fragment(self, value):
        self._fragment = value, sh.GL_FRAGMENT_SHADER

    @property
    def program(self):
        try:
            self._program
        except AttributeError:
            msg = 'Program not available, you must compile the shaders first'
            raise RenderException(msg)

        return self._program

    def compile(self):
        log.info('compiling and linking shader programs')

        if not hasattr(gl, 'glUseProgram'):
            msg = 'Missing shader objects'
            raise RenderException(msg)

        shader = self.vertex, self.fragment
        shader = [(open(s[0], 'r').read(), s[1]) for s in shader]
        shader = [sh.compileShader(*s) for s in shader]

        self._program = sh.compileProgram(*shader)

    def sendUniformVector(self, name, val):
        vecp = self._getUniformPointer(name)
        setter = getattr(gl, 'glUniform%dfv' % len(val))
        setter(vecp, 1, val)

    def sendUniformMatrix(self, name, val, dims):
        matp = self._getUniformPointer(name)
        setter = getattr(gl, 'glUniformMatrix%dfv' % dims)
        setter(matp, 1, gl.GL_TRUE, val)

    def getAttributePointer(self, name):
        return self._getPointer(name, 'attribute', gl.glGetAttribLocation)


class Renderer(object):

    def _emit(self, name, *args, **kwargs):
        for handler in self._handler:
            handle = getattr(handler, 'on' + name.capitalize())
            handle(*args, **kwargs)

    def _mvpmat(self):
        self._lastdimension = self.dimension

        offset = self.dimension / 2.
        mtrans = np.array([
            [1, 0, 0, -offset],
            [0, 1, 0, -offset],
            [0, 0, 1, 0],
            [0, 0, 0, 1]], 'f')

        scale = 1. / offset
        mscale = np.array([
            [scale, 0, 0, 0],
            [0, -scale, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]], 'f')

        return np.dot(mscale, mtrans)

    def _spline(self, points):
        converge = []

        def interpolate(points, t):
            f = lambda c: c[0] + t * (c[1] - c[0])
            l = [zip(c, c[1:]) for c in zip(*points)]
            return zip(*[map(f, xs) for xs in l])

        def rec(pts, d, right=False):
            if d == 0:
                converge.extend(pts)
                return

            columns = [pts]
            while len(columns[-1]) > 1:
                col = interpolate(columns[-1], 0.5)
                columns.append(col)

            rec([c[0] for c in columns], d - 1)
            rec([c[-1] for c in columns][::-1], d - 1)

        rec(points, self._rounds)
        return converge[::-1]

    def __init__(self):
        self._handler = []
        self._vobjs = []
        self._shader = Shader()

        # number of recursion steps when
        # gpu interpolation is turned off
        self._rounds = 6

        # indicates if the mvpmat
        # must be recalculated
        self._lastdimension = 0

    @property
    def cpoly(self):
        return self._cpoly

    @cpoly.setter
    def cpoly(self, cpoly):
        self._cpoly = cpoly
        self._splines = vertex.VertexObject(512)
        self._vobjs = [cpoly, self._splines]

    @property
    def shader(self):
        return self._shader

    @shader.setter
    def shader(self, value):
        self._shader = value

    @property
    def dimension(self):
        return self._dimension

    @dimension.setter
    def dimension(self, d):
        self._dimension = d

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        self._background = value
        gl.glClearColor(*value)

    @property
    def cpolyColor(self):
        return self._cpolyColor

    @cpolyColor.setter
    def cpolyColor(self, value):
        self._cpolyColor = value
        self._cpoly.color = value

    @property
    def splineColor(self):
        return self._splineColor

    @splineColor.setter
    def splineColor(self, value):
        self._splineColor = value
        self._splines.color = value

    @property
    def gpu(self):
        return self._gpu

    @gpu.setter
    def gpu(self, value):
        self._gpu = value

    def addHandler(self, handler):
        self._handler.append(handler)

    def repaint(self):
        self._emit('repaint')

    def render(self):
        log.trace('rendering %d vertex objects', len(self._vobjs))

        gl.glUseProgram(self.shader.program)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        #
        #   recalculate dimension mapping
        #
        if (self._lastdimension != self.dimension):
            log.trace('recalulating model view matrix with %d', self.dimension)
            self.shader.sendUniformMatrix('mvpmat', self._mvpmat(), 4)
            gl.glViewport(0, 0, self.dimension, self.dimension)

        #
        #   interpolate new curve segments
        #
        if not self.gpu:
            pcount = self.cpoly.size
            if pcount > 3 and (pcount - 1) % 3 == 0:
                log.trace('building new curve segment')
                cpoints = self.cpoly.get(4)
                spline = self._spline(cpoints)
                self._splines.addPoints(*spline)
                print spline[-5]

        #
        #   draw vertex buffers
        #
        for vobj in self._vobjs:
            log.trace('rendering %d vertices', vobj.size)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

            vertices = vobj.vbo
            vpointer = self.shader.getAttributePointer('vertex')
            vertices.bind()

            # send vertices
            gl.glEnableVertexAttribArray(vpointer)
            gl.glVertexAttribPointer(
                vpointer, 2, gl.GL_FLOAT, False, 0,
                gl.GLvoidp(4 * vobj.vertexOffset))
                # note: GL_FLOAT is defined to always
                # be 32 bit (4 byte) in size
            gl.glDrawArrays(gl.GL_LINE_STRIP, 0, vobj.size)

            # send colors
            self.shader.sendUniformVector('ucolor', vobj.color)
            vertices.unbind()

        # reset state
        gl.glFlush()
