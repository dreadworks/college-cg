#!/usr/bin/env python
# -*- coding: utf-8 -*-


import OpenGL.GLUT as glt


class Window(object):

    def __init__(self, name):
        self._lastsize = 0
        self._name = name

        glt.glutInit()
        glt.glutInitDisplayString("rgba double")
        # glt.glutInitContextVersion(3, 2)
        # glt.glutInitContextProfile(glt.GLUT_CORE_PROFILE)

    @property
    def name(self):
        return self._name

    @property
    def renderer(self):
        return self._renderer

    @renderer.setter
    def renderer(self, r):

        # create proxy function accessing
        # the render method to do things
        # before and after every rendering step
        def proxy():
            r.render()
            glt.glutSwapBuffers()

        self._renderer = r
        r.addHandler(self)

        glt.glutInitWindowSize(r.dimension, r.dimension)
        glt.glutCreateWindow(self.name)
        glt.glutDisplayFunc(proxy)

    @property
    def handler(self):
        return self._handler

    @handler.setter
    def handler(self, h):
        self._handler = h

        # mapping
        glt.glutMouseFunc(h.onMouseClicked)
        glt.glutReshapeFunc(h.onReshape)
        glt.glutKeyboardFunc(h.onKeyPress)

        # create menu
        glt.glutCreateMenu(h.onMenuClick)
        for k, v in h.menuItems.items():
            glt.glutAddMenuEntry(k, v)
        glt.glutAttachMenu(glt.GLUT_RIGHT_BUTTON)

    def show(self):
        glt.glutMainLoop()

    def reshape(self, size):
        if (size != self._lastsize):
            glt.glutReshapeWindow(size, size)
            self._lastsize = size

    # invoked by self.renderer
    def onRepaint(self):
        glt.glutPostRedisplay()
