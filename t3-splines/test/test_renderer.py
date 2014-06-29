# -*- coding: utf-8 -*-

import render
import unittest


class TestHandler():

    def __init__(self, callback):
        self._callback = callback

    def onRepaint(self):
        self._callback()


class RendererTest(unittest.TestCase):

    def setUp(self):
        self.renderer = render.Renderer()

    def testDimension(self):
        r = self.renderer
        dim = 500, 500
        r.dimension = dim
        self.assertEquals(r.dimension, dim)

    def testEventEmitter(self):
        r = self.renderer
        invoked = {'y': False}

        def callback():
            invoked['y'] = True

        handler = TestHandler(callback)
        r.addHandler(handler)
        r.repaint()

        self.assertTrue(invoked['y'])
