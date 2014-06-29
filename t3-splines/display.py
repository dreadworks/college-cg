#!/usr/bin/env python
# -*- coding: utf-8 -*-


import OpenGL.GLUT as glt


class Window(object):

    def __init__(self, name):
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
        # the renderer method to do things
        # before and after every rendering step
        def proxy():
            r.render()
            glt.glutSwapBuffers()

        self._renderer = r
        r.addHandler(self)

        glt.glutInitWindowSize(*r.dimension)
        glt.glutCreateWindow(self.name)
        glt.glutDisplayFunc(proxy)

    def show(self):
        glt.glutMainLoop()

    # invoked by self.renderer
    def onRepaint(self):
        glt.glutPostRedisplay()
