#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import argparse
from OpenGL import GLUT as glt


import render
import parser
import geometry
from util import LOG as logger


"""

Main Module, TODO docs

"""


def parse_args():
    """
    Parse command line arguments.
    """
    argp = argparse.ArgumentParser(
        description="""
            Render arbitrary .obj files with OpenGL.
            Currently the .obj directives o, v, vn,
            f and s are supported.
        """)

    argp.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='switch to verbose mode')

    argp.add_argument(
        'filename',
        type=str,
        help='obj file')

    # optional configuration
    argp.add_argument(
        '-r', '--res',
        type=str,
        default='500x500',
        help='window size e.g. "500x500"')

    argp.add_argument(
        '-s', '--shading',
        type=str,
        choices=['grid', 'flat', 'gouraud', 'phong'],
        default='gouraud',
        help='shading mode')

    return argp.parse_args()


def main(argv):
    args = parse_args()
    print args

    if args.verbose:
        logger.setVerbose()

    # determine window size
    ratio = map(int, args.res.split('x'))

    #
    #   INITIALIZE GLUT
    #
    cwd = os.getcwd()
    glt.glutInit([])
    os.chdir(cwd)

    glt.glutInitDisplayMode(
        glt.GLUT_DEPTH |
        glt.GLUT_DOUBLE |
        glt.GLUT_RGB)
    glt.glutInitWindowSize(*ratio)
    glt.glutCreateWindow("Object Viewer")

    #
    #   CREATE SCENE
    #
    scene = render.Scene.Instance()
    scene.setShading(args.shading)
    scene.setBackground((0.3, 0.3, 0.3, 0.))
    scene.callback = glt.glutSwapBuffers

    # create entities
    for obj in parser.ObjParser(args.filename).objects:
        polyhedron = geometry.Polyhedron(obj)
        scene.addEntity(polyhedron)

    #
    #   BIND HANDLER
    #
    def rotate():  # TODO remove
        for ent in scene.entities:
            ent.geometry.angle += 1
        glt.glutPostRedisplay()

    glt.glutDisplayFunc(scene.render)
    glt.glutIdleFunc(rotate)

    # dispatch
    glt.glutMainLoop()


if __name__ == '__main__':
    main(sys.argv)
