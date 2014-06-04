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
    Parses wavefront obj files.

    Currently supported:
      v, vn, f, s, o

    Ignored:
      usemtl

    """
    class Obj(object):
        """
        Parser for obj entity definitions. This
        is the whole obj file with zero or one
        "o" directives or the part of the obj
        file denoted by "o <name>".

        """

        def _parse(self, line):
            """
            Takes a line and saves the data
            found into the internal data structures.

            :param line: One line of the obj file
            :returns: None
            :rtype: None

            """
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
                    # 'f v/vt/vn' case
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
                    return

            #
            #   IGNORE
            #
            if dtype == 'usemtl':
                fmt = dtype, data
                log('ignoring directive %s with data %s' % fmt)
                return

            #
            #   NOT FOUND
            #
            msg = 'Could not map directive "%s"'
            raise ParserException(msg % dtype)

        def _smooth(self, group):
            """
            Calculates a new normal for a vertex
            based on all the surface normals on
            that particular point. The provided
            group determines the range of faces
            where the smoothing has to be applied.

            :param group: Tuple denoting the smoothing range
            :returns: None
            :rtype: None

            """
            log('smoothing normals between %d and %d' % group)

            for i in range(*group):
                v = self._faces[i][0]

                # cache miss
                if not type(self._v2vn[v]) is int:

                    # obtain normals
                    normals = self._v2vn[v]
                    normals = map(lambda i: self._normals[i], normals)

                    # calculate average normal
                    smoothed = sum(normals) / len(normals)
                    smoothed = smoothed / np.linalg.norm(smoothed)

                    # save smoothed normal
                    self._normals.append(smoothed)
                    self._v2vn[v] = len(self._normals) - 1
                    self.stats['smoothed normals'] += 1

                # save new vn to the faces (v, vn) tuple
                self._faces[i] = self._faces[i][0], self._v2vn[v]

        def __init__(self, name, data):
            """
            Initialize the object parser and
            parse the file provided.

            :param name: Name of the object
            :param data: List of strings with obj definitions
            :returns: self
            :rtype: parser.ObjParser.Obj

            """
            self._name = name

            # used for an efficient calculation
            # of smoothed surfaces and to retrieve
            # normals per vertex when serving faces
            self._v2vn = {}

            # just for statistics
            self.stats = {
                'calculated normals': 0,
                'smoothed normals': 0}

            # enumerations in obj's begin
            # with value 1 (for whatever reason...)
            # hence the None element.
            self._vertices = [None]   # [None, (x, y, z)₀, ...] ()₀ is np.array
            self._normals = [None]    # [None, (x, y, z)₀, ...] ()₀ is np.array
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
                try:
                    self._parse(line)
                except Exception as e:
                    msg = 'Could not parse line "%s"\nbecause of %s: %s'
                    fmt = (line, type(e), str(e))
                    raise ParserException(msg % fmt)

            # if smoothing never got
            # explicitly turned off
            if len(self._smoothing[-1]) == 1:
                self._smoothing[-1] += (len(self._faces),)

            # smooth if necessary
            for group in self._smoothing:
                self._smooth(group)

            # for -verbose
            fmt = [len(self._vertices), len(self._normals)]
            fmt = tuple(map(lambda x: x - 1, fmt))
            log('got %d vertices and %d normals' % fmt)

            fmt = len(self._faces)
            log('got %d vertex/vertex normal pairs for faces' % fmt)

            fmt = self.stats['calculated normals']
            log('calculated %d normals' % fmt)

            fmt = self.stats['smoothed normals']
            fmt = fmt, sum([y - x for x, y in self._smoothing])
            log('calculated %d smoothed normals of %d definitions' % fmt)

        #
        #   PROPERTIES
        #
        # @property
        def name(self):
            """
            Returns the objects name

            :returns: The name
            :rtype: string

            """
            return self._name

        @property
        def vertices(self):
            """
            Returns a numpy array of vertex coordinates.

            :returns: Vertex coordinates
            :rtype: numpy.Array

            """
            return np.array(self._vertices[1:], 'f')

        @property
        def faces(self):
            """
            Returns the faces as a numpy array consisting
            of v, vn pairs, where v are vertex coordinates
            and vn surface normal coordinates.

            :returns: Geometrical description of faces
            :rtype: numpy.Array

            """
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
        """
        Parses an wavefront obj file. For every
        defined object an ObjParser.Obj object
        is created.

        :param fname: File name
        :returns: self
        :rtype: parser.ObjParser

        """
        log('parsing %s' % fname)

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
        """
        Return all parsed objects

        :returns: Parsed objects
        :rtype: List of parse.ObjParser.Obj objects

        """
        return self._objects
