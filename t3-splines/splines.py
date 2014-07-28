#!/usr/bin/env python
# -*- coding: utf-8 -*-

import render
import vertex
import display

import json
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

    def _addPoint(self, x, y):
        renderer = self.window.renderer
        vertices = renderer.cpoly

        vertices.addPoint(x, y)

        if renderer.gpu:
            renderer.splines.addPoint(x, y)

        else:
            pcount = vertices.size
            if pcount > 3 and (pcount - 1) % 3 == 0:
                log.trace('building new curve segment')
                spline = self._spline(vertices.get(4))
                renderer.splines.addPoints(*spline)

    def __init__(self, window):
        self._window = window

        # number of recursion steps when
        # gpu interpolation is turned off
        self._rounds = 6

    @property
    def window(self):
        return self._window

    @property
    def menuItems(self):
        return {
            'open': 0,
            'save': 1
        }

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
            self._addPoint(x, y)
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

    def onMenuClick(self, action):
        if action not in self.menuItems.values():
            return

        actions = self.menuItems
        renderer = self.window.renderer
        location = 'data/test.json'

        # these properties are automatically
        # saved and retrieved from the renderer
        mappedProperties = [
            'dimension',
            'cpolyColor',
            'splineColor']

        #
        #   SAVE TO FILE
        #
        if action == actions['save']:
            log.trace('saving to %s', location)
            data = {}

            data['cpoly'] = renderer.cpoly.all()
            for prop in mappedProperties:
                data[prop] = getattr(renderer, prop)

            data = json.dumps(data, indent=4, separators=(',', ': '))
            with open(location, 'w') as f:
                f.write(data)

        #
        #   LOAD FROM FILE
        #
        if action == actions['open']:
            log.trace('loading from %s', location)

            with open(location, 'r') as f:
                data = json.loads(f.read())

            renderer.cpoly = vertex.VertexObject(BUFSIZE)
            for p in data['cpoly'][::-1]:
                self._addPoint(*p)

            for prop in mappedProperties:
                setattr(renderer, prop, data[prop])

            self.window.reshape(renderer.dimension)

        return 0


def main():
    LOG.setVerbose()

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
    renderer.shader.geometry = 'shader/bezier.geom'
    renderer.shader.fragment = 'shader/std.frag'
    renderer.shader.compile()

    # appearance
    renderer.background = (.2, .2, .2, 0.)
    renderer.cpolyColor = (1., .6, 0., 0.)
    renderer.splineColor = (0., .6, 1., 0.)

    window.show()


if __name__ == '__main__':
    main()
