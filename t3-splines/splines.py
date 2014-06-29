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

    def __init__(self):
        pass


def main():
    LOG.setVerbose()

    # initialize data object
    vobj = vertex.VertexObject(BUFSIZE)

    # configure renderer
    log.info('creating renderer')
    renderer = render.Renderer()
    renderer.dimension = 500, 500
    renderer.vobj = vobj

    # create window
    log.info('creating window')
    window = display.Window('Bezier Splines')
    window.renderer = renderer
    window.handler = Handler()

    # configure shader
    renderer.shader.vertex = 'shader/std.vert'
    renderer.shader.fragment = 'shader/std.frag'
    renderer.shader.compile()

    window.show()


if __name__ == '__main__':
    main()
