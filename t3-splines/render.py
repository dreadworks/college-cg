#!/usr/bin/env python
# -*- coding: utf-8 -*-


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

    def _getUniformPointer(self, name):
        cache = self._varcache
        if not name in cache:
            pointer = gl.glGetUniformLocation(self.program, name)
            cache[name] = pointer
        else:
            pointer = cache[name]
        return pointer

    def __init__(self):
        self._varcache = {}

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
        setter = getattr(gl, 'glUniform%df' % len(val))
        setter(vecp, val)

    def sendUniformMatrix(self, name, val, dims):
        matp = self._getUniformPointer(name)
        setter = getattr(gl, 'glUniformMatrix%dfv' % dims)
        setter(matp, 1, gl.GL_TRUE, val)


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

    def __init__(self):
        self._handler = []
        self._shader = Shader()

        # indicates if the mvpmat
        # must be recalculated
        self._lastdimension = 0

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
    def dimension(self, value):
        self._dimension = value

    def addHandler(self, handler):
        self._handler.append(handler)

    def repaint(self):
        self._emit('repaint')

    def render(self):
        log.trace('rendering %d points', self.vobj.size)
        vertices = self.vobj.vbo

        gl.glUseProgram(self.shader.program)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # //

        if (self._lastdimension != self.dimension):
            self.shader.sendUniformMatrix('mvpmat', self._mvpmat(), 4)

        # //

        # set draw style
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        # render vertex buffer
        vertices.bind()
        # gl.glVertexPointer(4, gl.GL_FLOAT, 16, vertices)
        gl.glVertexPointerf(vertices)
        gl.glDrawArrays(gl.GL_LINE_STRIP, 0, self.vobj.size)
        vertices.unbind()

        # reset state
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
