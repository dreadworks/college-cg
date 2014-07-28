#!/usr/bin/env python
# -*- coding: utf-8 -*-

import vertex

import numpy as np
import OpenGL.GL as gl
import OpenGL.GL.shaders as sh

# i have not been able to activate
# the core profile on my machine...
import OpenGL.GL.EXT.geometry_shader4 as extgs4


from util import LOG
log = LOG.out


class RenderException(Exception):

    def __str__(self):
        return self._msg

    def __init__(self, msg):
        self._msg = msg


class Shader(object):

    def _link(self, shader, *shaderkeys):
        prog = gl.glCreateProgram()
        for name in shaderkeys:
            gl.glAttachShader(prog, shader[name])

        if 'geometry' in shaderkeys:
            extgs4.glProgramParameteriEXT(
                prog, extgs4.GL_GEOMETRY_INPUT_TYPE_EXT,
                gl.GL_LINES_ADJACENCY)

            extgs4.glProgramParameteriEXT(
                prog, extgs4.GL_GEOMETRY_OUTPUT_TYPE_EXT,
                gl.GL_LINE_STRIP)

            extgs4.glProgramParameteriEXT(
                prog, extgs4.GL_GEOMETRY_VERTICES_OUT_EXT,
                200)

        gl.glLinkProgram(prog)

        log.info(
            'linked program %s: %s',
            shaderkeys,
            gl.glGetProgramInfoLog(prog) or 'success')

        return prog

    def _getPointer(self, name, vtype, getter):
        cache = self._cache[vtype]

        if not name in cache:
            pointer = getter(self.program, name)
            cache[name] = pointer

        else:
            pointer = cache[name]

        log.trace('acquired %s pointer "%s": %s', vtype, name, pointer)
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

    @property
    def geometry(self):
        return self._geometry

    @geometry.setter
    def geometry(self, value):
        self._geometry = value, extgs4.GL_GEOMETRY_SHADER_EXT

    @property
    def fragment(self):
        return self._fragment

    @fragment.setter
    def fragment(self, value):
        self._fragment = value, sh.GL_FRAGMENT_SHADER

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, value):
        self._program = value

    @property
    def stdProgram(self):
        try:
            self._stdProgram
        except AttributeError:
            msg = 'Program not available, you must compile the shaders first'
            raise RenderException(msg)

        return self._stdProgram

    @property
    def bezierProgram(self):
        return self._bezierProgram

    @bezierProgram.setter
    def bezierProgram(self, value):
        self._bezierProgram = value

    def compile(self):
        log.info('compiling and linking shader programs')

        if not hasattr(gl, 'glUseProgram'):
            msg = 'Missing shader objects'
            raise RenderException(msg)

        # assemble raw configuration
        shader = {
            'vertex': self.vertex,
            'geometry': self.geometry,
            'fragment': self.fragment
        }

        # map configuration to shader objects
        for name, conf in shader.items():
            sfile, sprog = conf

            sprog = gl.glCreateShader(sprog)
            with open(sfile, 'r') as f:
                sfile = f.read()

            gl.glShaderSource(sprog, sfile)
            gl.glCompileShader(sprog)

            shader[name] = sprog
            log.info('compiling %s shader: %s',
                     name, gl.glGetShaderInfoLog(sprog) or 'success')

        self._stdProgram = self._link(
            shader, 'vertex', 'fragment')

        self._bezierProgram = self._link(
            shader, 'vertex', 'geometry', 'fragment')

    def sendUniformValue(self, name, val, dtype='f'):
        vp = self._getUniformPointer(name)
        setter = getattr(gl, 'glUniform1%s' % dtype)
        setter(vp, val)

    def sendUniformVector(self, name, val, dtype='f'):
        dims = len(val)
        vecp = self._getUniformPointer(name)
        setter = getattr(gl, 'glUniform%d%s' % (dims, dtype))
        setter(vecp, *val)

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
            [0, 0, 0, 1]], dtype=np.float32)

        scale = 1. / offset
        mscale = np.array([
            [scale, 0, 0, 0],
            [0, -scale, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]], dtype=np.float32)

        return np.dot(mscale, mtrans)

    #
    #   RENDER VBOS
    #
    def _render(self, vobj, mode):
        log.trace('rendering %d vertices', vobj.size)
        gl.glUseProgram(self.shader.program)

        # send interpolation informations
        if self.gpu and self.shader.program is self.shader.bezierProgram:
            self.shader.sendUniformValue("interpolations", 4)

        # send colors
        self.shader.sendUniformVector('color', vobj.color)

        #
        #   recalculate model view projection matrix
        #
        if (self._lastdimension != self.dimension):
            log.trace('recalulating model view matrix with %d', self.dimension)
            self.shader.sendUniformMatrix('mvpmat', self._mvpmat(), 4)
            gl.glViewport(0, 0, self.dimension, self.dimension)

        #
        #   set vertices
        #
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

        gl.glDrawArrays(mode, 0, vobj.size)
        vertices.unbind()

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
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

        # control polygon
        self.shader.program = self.shader.stdProgram
        self._render(self.cpoly, gl.GL_LINE_STRIP)

        # splines
        if self.gpu:
            self.shader.program = self.shader.bezierProgram
            self._render(self.splines, gl.GL_LINE_STRIP_ADJACENCY)
        else:
            self._render(self.splines, gl.GL_LINE_STRIP)

        # reset state
        gl.glFlush()
