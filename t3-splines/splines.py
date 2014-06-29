#!/usr/bin/env python
# -*- coding: utf-8 -*-

import render
import vertex
import display

from util import LOG
log = LOG.out


# initial size of the vertex buffer
# (real size = BUFSIZE * sizeof(float) * 3)
BUFSIZE = 128


class Handler(object):

    def __init__(self, renderer):
        self._renderer = renderer

    @property
    def renderer(self):
        return self._renderer

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
            vertices = self.renderer.vobj
            vertices.add(x, y)
            self.renderer.repaint()


def main():
    LOG.setVerbose()

    # initialize data object
    vobj = vertex.VertexObject(BUFSIZE)

    # configure renderer
    log.info('creating renderer')
    renderer = render.Renderer()
    renderer.dimension = 500
    renderer.vobj = vobj

    # create window
    log.info('creating window')
    window = display.Window('Bezier Splines')
    window.renderer = renderer
    window.handler = Handler(renderer)

    # configure shader
    renderer.shader.vertex = 'shader/std.vert'
    renderer.shader.fragment = 'shader/std.frag'
    renderer.shader.compile()

    window.show()


if __name__ == '__main__':
    main()
