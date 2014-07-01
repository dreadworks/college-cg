#!/usr/bin/env python
# -*- coding: utf-8 -*-

import render
import vertex
import display

from util import LOG
log = LOG.out


# initial size of the vertex buffer for
# the control polygon and (if necessary) the
# interpolated bezier spline.
# (real size = BUFSIZE * sizeof(float) * 2)
BUFSIZE = 128


class Handler(object):

    def __init__(self, window):
        self._window = window

    @property
    def window(self):
        return self._window

    def onMouseClicked(self, btn, up, x, y):
        """
        Event fired when a mouse button gets
        pressed or released.

        :param btn: 0, 1, 2 as mapped by GLUT
        :param up: 0 or 1 if pressed or released
        :param x: Cursors x-coordinate
        :param y: Cursors y-coordinate
        :returns: None
        :rtype: None

        """
        if not up:
            log.info('registered mouse click event on %d, %d', x, y)
            vertices = self.window.renderer.ctrlPolygon
            vertices.addPoint(x, y)
            self.window.renderer.repaint()

    def onReshape(self, width, height):
        renderer = self.window.renderer
        renderer.dimension = max(width, height)
        self.window.reshape(renderer.dimension)
        renderer.repaint()


def main():
    LOG.setTrace()

    # initialize data object
    cpoly = vertex.VertexObject(BUFSIZE)

    # configure renderer
    log.info('creating renderer')
    renderer = render.Renderer()
    renderer.ctrlPolygon = cpoly
    renderer.useGPU = False
    renderer.dimension = 500

    # create window
    log.info('creating window')
    window = display.Window('Bezier Splines')
    window.renderer = renderer
    window.handler = Handler(window)

    # configure shader
    renderer.shader.vertex = 'shader/std.vert'
    renderer.shader.fragment = 'shader/std.frag'
    renderer.shader.compile()

    window.show()


if __name__ == '__main__':
    main()
