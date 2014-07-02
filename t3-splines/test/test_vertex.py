# -*- coding: utf-8 -*-

import vertex
import unittest


class VertexTest(unittest.TestCase):

    BUFSIZE = vertex.VertexObject.OFFSET

    def setUp(self):
        self.vobj = vertex.VertexObject(VertexTest.BUFSIZE)

    def testInitialization(self):
        o = self.vobj
        self.assertEquals(o.size, 0)

    def testPushPop(self):
        o = self.vobj

        for p in zip(range(3), range(3)):
            o.addPoint(*p)
        self.assertEquals(o.size, 3)

        o.undo()
        self.assertEquals(o.size, 2)

        o.undo()
        o.addPoint(1, 1)
        o.undo()
        o.undo()

        self.assertEquals(o.size, 0)

    def testPushCollection(self):
        o = self.vobj

        for i in range(1, 10):
            coll = zip(range(i), range(i))
            o.addPoints(*coll)

        self.assertEquals(o.size, 45)  # 9 * 10 / 2

        for _ in range(1, 10):
            o.undo()

        self.assertEquals(o.size, 0)

    def testGet(self):
        o = self.vobj

        for p in zip(range(3), range(3)):
            o.addPoint(*p)

        items = o.get(2)
        self.assertEquals(items[0], (2., 2.))
        self.assertEquals(items[1], (1., 1.))

        o.empty()

    def testBufferIncrease(self):
        o = self.vobj
        c = 5

        for p in zip(range(c), range(c)):
            o.addPoint(*p)

        self.assertEquals(o.size, 5)

        amount = c / VertexTest.BUFSIZE + 2  # + 2 because ceil and offset
        self.assertEquals(len(o.vbo.data), VertexTest.BUFSIZE * amount)

        for _ in range(5):
            o.undo()

    def testBufferDecrease(self):
        o = self.vobj

        for _ in range(15):
            o.addPoint(0, 0)

        for _ in range(15):
            o.undo()

        self.assertEquals(o.size, 0)
        self.assertEquals(len(o.vbo.data), VertexTest.BUFSIZE * 2)

    def testEmptyWithBufferDecrease(self):
        o = self.vobj
        for _ in range(VertexTest.BUFSIZE * 3 - 1):
            o.addPoint(1, 1)

        o.empty()
        self.assertEquals(o.size, 0)
        self.assertEquals(len(o.vbo.data), VertexTest.BUFSIZE)

    def testEmptyWithoutBufferDecrease(self):
        o = self.vobj
        for _ in range(VertexTest.BUFSIZE * 3 - 1):
            o.addPoint(1, 1)

        o.empty(False)
        self.assertEquals(o.size, 0)
        self.assertEquals(len(o.vbo.data), VertexTest.BUFSIZE * 4)

    def testColor(self):
        o = self.vobj

        c = (1, 2, 3, 4)
        o.color = c

        self.assertEquals(o.color, c)
