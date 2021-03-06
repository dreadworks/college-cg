#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import argparse
from OpenGL import GLUT as glt


import util
import render
import parser
import geometry

from util import LOG as logger
log, trace = logger.out.info, logger.out.trace

"""

This is the main application module. It handles
the parsing of command line arguments and initializes
all GLUT-related things. It operates as the dispatcher
for GUI-Events and repaint cicles but the main program
runs in render.py.

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
        '-t', '--trace',
        action='store_true',
        help='very very verbose')

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
        choices=['grid', 'flat', 'smooth'],
        default='smooth',
        help='shading mode')

    argp.add_argument(
        '--fow', type=int,
        default=45,
        help='field of view for projective perspective')

    return argp.parse_args()


def main(argv):
    """

    Program entry point. This function blocks.

    :param argv: sys.argv (or some mock)
    :returns: None
    :rtype: None

    """
    delim = '\n' + '- ' * 40
    args = parse_args()

    if args.verbose:
        logger.setVerbose()

    if args.trace:
        logger.setTrace()

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
    glt.glutCreateWindow("Rendering %s" % args.filename.rstrip('.obj'))

    #
    #   CREATE SCENE
    #
    log('initializing scene:%s' % delim)
    scene = render.Scene.Instance()
    scene.setShading(args.shading)
    scene.callback = glt.glutSwapBuffers
    scene.repaint = glt.glutPostRedisplay

    # alter appearance
    scene.background = util.Color().hex(0x33333300)
    light = scene.createLight()
    light.position = 0.5, 2., 0.5

    # create camera
    cam = render.Camera.Instance()
    cam.fow, cam.ratio = args.fow, ratio
    cam.mode, cam.offset = cam.ORTHOGONALLY, 1
    scene.camera = cam

    # create entities
    log('parsing and inintializing geometries:%s' % delim)
    for obj in parser.ObjParser(args.filename).objects:
        polyhedron = geometry.Polyhedron(obj)
        ent = scene.addEntity(polyhedron)
        ent.material.ambient = util.Color().rgba(0, 123, 255, 0.5)
        # ent.material.specular = .2, .2, .2, .5
        # ent.material.shininess = 100

    #
    #   BIND HANDLER
    #
    trace('listening:%s' % delim)
    glt.glutMouseFunc(scene.evt.mouseClicked)
    glt.glutMotionFunc(scene.evt.mouseMoved)
    glt.glutKeyboardFunc(scene.evt.keyPressed)
    glt.glutReshapeFunc(scene.evt.reshape)

    # dispatch
    glt.glutDisplayFunc(scene.render)
    glt.glutMainLoop()


if __name__ == '__main__':
    main(sys.argv)
