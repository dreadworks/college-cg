#!/usr/bin/env python
# -*- coding: utf-8 -*-


import OpenGL.GLUT as glt


class Window(object):

    def __init__(self, name, size):
        self._name = name

        glt.glutInit()
        glt.glutInitDisplayMode(
            glt.GLUT_DOUBLE |
            glt.GLUT_RGBA |
            glt.GLUT_DEPTH)

    @property
    def name(self):
        return self._name

    @property
    def renderer(self):
        return self._renderer

    @renderer.setter
    def renderer(self, r):

        # create proxy function accessing
        # the renderer via closure to be able
        # to do things before and after every
        # rendering step
        def proxy():
            r.render()
            glt.glutSwapBuffers()

        self._renderer = r
        glt.glutDisplayFunc(proxy)

    def show(self):
        size = self.renderer.dimension
        glt.glutInitWindowSize(*size)
        glt.glutCreateWindow(self.name)
        glt.glutMainLoop()
