# -*- coding: utf-8 -*-

import vertex
import unittest


class VertexTest(unittest.TestCase):

    BUFSIZE = 4

    def setUp(self):
        self.vobj = vertex.VertexObject(VertexTest.BUFSIZE)

    def testInitialization(self):
        o = self.vobj
        self.assertEquals(o.size, 0)

    def testPushPop(self):
        o = self.vobj

        for p in zip(range(3), range(3)):
            o.add(*p)
        self.assertEquals(o.size, 3)

        o.undo()
        self.assertEquals(o.size, 2)

        o.undo()
        o.add(1, 1)
        o.undo()
        o.undo()

        self.assertEquals(o.size, 0)

    def testBufferIncrease(self):
        o = self.vobj
        for p in zip(range(5), range(5)):
            o.add(*p)

        self.assertEquals(o.size, 5)
        self.assertEquals(len(o.vbo.data), VertexTest.BUFSIZE * 2)

        for _ in range(5):
            o.undo()

    def testBufferDecrease(self):
        o = self.vobj

        for _ in range(15):
            o.add(0, 0)

        for _ in range(15):
            o.undo()

        self.assertEquals(o.size, 0)
        self.assertEquals(len(o.vbo.data), VertexTest.BUFSIZE)
