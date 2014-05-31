#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import numpy as np


from util import LOG
log = LOG.out.info


"""

Parser Library.

Every class gets instantiated with the
name of the file that should be parsed.
Every instance of a parser is bound to
a file and thus maintains the files data.

The classes should handle their parsing
internally without the need to invoke an
extra method that handles that actual parsing.
Even though this makes error handling of
the parsing more complicated (from the users
perspective), it enables the possibility
to work on very large data without the need
to store everything in memory at once.

"""


class ParserException(Exception):

    def __str__(self):
        return self.msg

    def __init__(self, msg):
        self.msg = msg


#
#
#
#
class ObjParser(object):
    """
    Currently supported:
      v, vn, f, s, o

    Ignored:
      usemtl

    """
    class Obj(object):
        """

        TODO docs

        """
        stats = {
            'calculated normals': 0
        }

        def _parse(self, line):
            dtype, data = re.split(r' ', line, maxsplit=1)
            data = data.strip()

            #
            #   VERTICES
            #
            if dtype == 'v':
                data = map(float, data.split())
                self._vertices.append(np.array(data, 'f'))
                return

            #
            #   NORMALS
            #
            if dtype == 'vn':
                data = map(float, data.split())
                self._normals.append(np.array(data, 'f'))
                return

            #
            #   FACES
            #
            # save indices of vertices and normals
            # in self._vertices & self._normals
            # and map the vertex to a set of points
            # in self._v2vn
            if dtype == 'f':
                data = map(lambda s: s.split('/'), data.split())
                vertices = map(lambda l: int(l[0]), data)
                normals = []
                normal = None  # cache

                for i, pair in enumerate(data):
                    if len(pair) == 3:
                        index = int(pair[2])

                    #
                    #   calculate new surface normal
                    #
                    else:

                        if normal is not None:
                            index = len(self._normals) - 1

                        else:
                            self.stats['calculated normals'] += 1

                            # retrieve point coordinates
                            v = map(lambda j: self._vertices[j], vertices)

                            # create normalized vectors spanning a plane
                            vectors = (v[0] - v[1]), (v[0] - v[2])

                            # the surface normal is the cross product
                            # of the two vectors spanning the plane
                            normal = np.cross(*vectors)
                            normal = normal / np.linalg.norm(normal)

                            index = len(self._normals)
                            self._normals.append(normal)

                    # save normals index
                    normals.append(index)
                    vnstore = self._v2vn.setdefault(vertices[i], [])
                    vnstore.append(index)

                self._faces += zip(vertices, normals)
                return

            #
            #   SMOOTHING GROUPS
            #
            if dtype == 's':
                g = self._smoothing[-1]
                facecount = len(self._faces)

                if data == 'off':
                    if len(g) == 1:
                        self._smoothing[-1] += (facecount,)
                    return

                if data == 'on':
                    if len(g) == 2:
                        self._smoothing.append((facecount,))

            #
            #   IGNORE
            #
            if dtype == 'usemtl':
                log('ignoring directive %s' % dtype)
                return

            #
            #   NOT FOUND
            #
            msg = 'Could not map directive "%s"'
            raise ParserException(msg % dtype)

        def __init__(self, name, data):
            self._name = name

            # used for an efficient calculation
            # of smoothed surfaces and to retrieve
            # normals per vertex when serving faces
            self._v2vn = {}

            # enumerations in obj's begin
            # with value 1 (for whatever reason...)
            # hence the None element.
            self._vertices = [None]   # [None, (x, y, z)₀, ...]
            self._normals = [None]    # [None, (x, y, z)₀, ...]
            self._smoothing = [(0,)]  # Ranges of faces where
                                      # smoothing is activated
            self._faces = []          # [(v₀, vn₀), (v₁, vn₁), ...],
                                      # v and vn as indices of elements in
                                      # self._vertices and self._normals

            # split data line-wise and remove
            # empty lines and comments
            sanitize = lambda s: s and not s.startswith('#')
            data = filter(sanitize, data.split('\n'))
            log('analyzing %d lines of raw data' % len(data))

            # analyze data line by line
            # note: len is an O(1) operation
            for line in data:
                self._parse(line)
                # try:
                #     self._parse(line)
                # except Exception as e:
                #     msg = 'Could not parse line "%s"\nbecause of %s: %s'
                #     fmt = (line, type(e), str(e))
                #     raise ParserException(msg % fmt)

            # if smoothing never got explicitly
            # turned off
            if len(self._smoothing[-1]) == 1:
                self._smoothing[-1] += (len(self._faces),)

            # for -verbose
            fmt = [len(self._vertices), len(self._normals)]
            fmt = tuple(map(lambda x: x - 1, fmt))
            log('got %d vertices and %d normals' % fmt)

            fmt = len(self._faces)
            log('got %d vertex/vertex normal pairs for faces' % fmt)

            fmt = self.stats['calculated normals']
            log('calculated %d normals' % fmt)

            fmt = (len(self._smoothing), self._smoothing)
            log('got %d smoothing range(s): %s' % fmt)

            # statistics
            _, normals = zip(* self._v2vn.items())
            normals = map(lambda l: float(len(l)), normals)
            log('faces per vertex: avg: %f, deviation: %f, variance: %f' % (
                np.average(normals), np.std(normals), np.var(normals)))

        #
        #   PROPERTIES
        #
        # @property
        def name(self):
            return self._name

        @property
        def vertices(self):
            return np.array(self._vertices[1:], 'f')

        @property
        def faces(self):
            v, vn = zip(*self._faces)
            v = map(lambda i: self._vertices[i], v)
            vn = map(lambda i: self._normals[i], vn)
            return np.array(zip(v, vn), 'f')

    #
    #
    #
    #
    #
    def __init__(self, fname):
        with open(fname) as f:
            data = f.read()
            self._objects = []
            add = self._objects.append

            log('parsing data of size %d' % len(data))
            objs = re.split(r'^o (.*)', data)

            # no 'o'-directive found
            if len(objs) == 1:
                add(ObjParser.Obj(fname.rstrip('.obj'), objs[0]))

            # multiple objects per obj
            for name, data in zip(objs[1::2], objs[2::2]):
                add(ObjParser.Obj(name, data))

            return

        raise ParserException("Could not open file")

    @property
    def objects(self):
        return self._objects
