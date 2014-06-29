#!/usr/bin/env python
# -*- coding: utf-8 -*-


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

    def __init__(self):
        pass

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


class Renderer(object):

    def _emit(self, name, *args, **kwargs):
        for handler in self._handler:
            handle = getattr(handler, 'on' + name.capitalize())
            handle(*args, **kwargs)

    def __init__(self):
        self._handler = []
        self._shader = Shader()

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
        log.info('rendering')
        vertices = self.vobj.vbo

        gl.glUseProgram(self.shader.program)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # TODO
        # reinitialize the modelview matrix
        # and pass them with the project matrix
        # to the vertex shader

        # set draw style
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        # render vertex buffer
        vertices.bind()
        gl.glVertexPointerf(vertices)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.vobj.size)
        vertices.unbind()

        # reset state
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
