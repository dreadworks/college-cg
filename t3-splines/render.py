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

    def sendUniformVector(self, name, val, dtype='f'):
        vecp = self._getUniformPointer(name)
        setter = getattr(gl, 'glUniform%d%sv' % (len(val), dtype))
        setter(vecp, 1, val)

    def sendUniformMatrix(self, name, val, dims, dtype='f'):
        matp = self._getUniformPointer(name)
        setter = getattr(gl, 'glUniformMatrix%d%sv' % (dims, dtype))
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

    #
    #   RENDER VBOS
    #
    def _render(self, vobj, draw):
        log.trace('rendering %d vertices', vobj.size)

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

        draw()

        # send colors
        self.shader.sendUniformVector('ucolor', vobj.color)
        vertices.unbind()

    def _renderCpoly(self):
        size = self.cpoly.size
        mode = gl.GL_LINE_STRIP
        draw = lambda: gl.glDrawArrays(mode, 0, size)

        self.shader.sendUniformVector('spline', [0], 'i')
        self._render(self.cpoly, draw)

    def _renderSplines(self):

        def draw():
            size = self.splines.size
            mode = gl.GL_LINE_STRIP

            if not self.gpu:
                gl.glDrawArrays(mode, 0, size)

            else:
                for i in range((size - 1) / 3):
                    gl.glDrawArrays(mode, i * 3, 4)

        self.shader.sendUniformVector('spline', [1], 'i')
        self._render(self.splines, draw)

    def __init__(self):
        self._handler = []
        self._shader = Shader()

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

    @property
    def splines(self):
        return self._splines

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
        log.trace('rendering vertex objects')

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
        #   draw vertex buffers
        #
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        # self._renderCpoly()
        self._renderSplines()

        # reset state
        gl.glFlush()
