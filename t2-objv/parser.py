#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


class Obj(dict):
    """
    The .obj parser is a pimped dictionary.
    Parsing is executed at instantiation.
    """

    def _map(self, dtype, data):
        # (Altered) Descriptions from http://paulbourke.net/dataformats/obj/

        #   VERTICES
        #
        # Specifies a geometric vertex and its x y z coordinates.
        # x y z are the x, y, and z coordinates for the vertex. These are
        # floating point numbers that define the position of the vertex in
        # three dimensions.
        if dtype == 'v':
            return tuple(map(float, data))

        #   VERTEX NORMALS
        #
        # Specifies a normal vector with components i, j, and k.
        # Vertex normals affect the smooth-shading and rendering of geometry.
        # For polygons, vertex normals are used in place of the actual facet
        # normals.  For surfaces, vertex normals are interpolated over the
        # entire surface and replace the actual analytic surface normal.
        if dtype == 'vn':
            return tuple(map(float, data))

        #   FACES
        #
        # Specifies a face element and its vertex reference number. You can
        # optionally include the texture vertex and vertex normal reference
        # numbers.
        # The reference numbers for the vertices, texture vertices, and
        # vertex normals must be separated by slashes (/). There is no space
        # between the number and the slash.
        #  - v is the reference number for a vertex in the face element. A
        #    minimum of three vertices are required.
        #  - vt (optional) is the reference number for a texture vertex in
        #    the face element. It always follows the first slash.
        #  - vn (optional) is the reference number for a vertex normal in the
        #    face element. It must always follow the second slash.
        if dtype == 'f':

            # convert every reference to a valid index
            indexmap = lambda t: None if not len(t) else int(t) - 1

            # split raw data at '/' and invoke indexmap for every element
            grind = lambda t: map(indexmap, t.split('/'))

            # apply mapping
            return tuple(map(grind, data))

        raise ParserException('Unknown directive %s' % dtype)

    def _store(self, raw):

        # TODO implement grouping (like s or g) -> search for 's off'

        try:
            dtype, x, y, z = raw.split()
        except ValueError:
            msg = 'Could not parse line "%s"' % raw
            raise ParserException(msg)

        store = self.setdefault(dtype, [])
        data = self._map(dtype, (x, y, z))
        store.append(data)

    def __init__(self, fname):
        with open(fname) as f:

            # eliminate empty lines
            lines = filter(lambda s: s.strip(), f.readlines())
            log('read %d non-empty lines from file' % len(lines))

            # save data to internal data structure
            map(self._store, lines)  # TODO error handling
            fmt = len(self.keys()), tuple(self.keys())
            log('read %d keys: %s' % fmt)

    @property
    def vertices(self):
        return self['v']

    def faces(self):
        # yields ((vertex1, normal1), ...)
        # where vertexi and normali are tuples of coordinates
        for face in self['f']:
            vertices, _, _ = zip(*face)
            yield map(lambda i: self['v'][i], vertices)
