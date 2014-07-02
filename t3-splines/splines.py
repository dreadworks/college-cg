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

    def _spline(self, points):
        converge = []

        def interpolate(points, t):
            f = lambda c: c[0] + t * (c[1] - c[0])
            l = [zip(c, c[1:]) for c in zip(*points)]
            return zip(*[map(f, xs) for xs in l])

        def rec(pts, d, right=False):
            if d == 0:
                converge.extend(pts)
                return

            columns = [pts]
            while len(columns[-1]) > 1:
                col = interpolate(columns[-1], 0.5)
                columns.append(col)

            rec([c[0] for c in columns], d - 1)
            rec([c[-1] for c in columns][::-1], d - 1)

        rec(points, self._rounds)
        return converge[::-1]

    def __init__(self, window):
        self._window = window

        # number of recursion steps when
        # gpu interpolation is turned off
        self._rounds = 6

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
            renderer = self.window.renderer
            vertices = renderer.cpoly

            vertices.addPoint(x, y)

            if not renderer.gpu:
                pcount = vertices.size
                if pcount > 3 and (pcount - 1) % 3 == 0:
                    log.trace('building new curve segment')
                    spline = self._spline(vertices.get(4))
                    renderer.splines.addPoints(*spline)

            self.window.renderer.repaint()

    def onReshape(self, width, height):
        renderer = self.window.renderer
        renderer.dimension = max(width, height)
        self.window.reshape(renderer.dimension)
        renderer.repaint()

    def onKeyPress(self, key, x, y):
        """
        Called when a key gets pressed.

        :param key: Key on the keyboard
        :param x: Cursors x-coordinate
        :param y: Cursors y-coordinate
        :returns: None
        :rtype: None

        """
        if key == 'd':
            renderer = self.window.renderer
            vertices = renderer.cpoly

            try:
                vertices.undo()
                if vertices.size % 3 == 0:
                    self.window.renderer.splines.undo()
                renderer.repaint()

            # thrown when vertices/splines .size == 0
            except vertex.VertexException:
                pass


def main():
    LOG.setTrace()

    # configure renderer
    log.info('creating renderer')
    renderer = render.Renderer()
    renderer.cpoly = vertex.VertexObject(BUFSIZE)
    renderer.dimension = 500
    renderer.gpu = False

    # create window
    log.info('creating window')
    window = display.Window('Bezier Splines')
    window.renderer = renderer
    window.handler = Handler(window)

    # configure shader
    renderer.shader.vertex = 'shader/std.vert'
    renderer.shader.fragment = 'shader/std.frag'
    renderer.shader.compile()

    # test
    # renderer.cpoly.addPoints(
    #    (400, 400), (400, 100), (100, 100), (100, 400))

    # appearance
    renderer.background = (.2, .2, .2, 0.)
    renderer.cpolyColor = (1., .6, 0., 0.)
    renderer.splineColor = (0., .6, 1., 0.)

    window.show()


if __name__ == '__main__':
    main()
