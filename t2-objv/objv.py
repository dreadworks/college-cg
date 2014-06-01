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
log = logger.out.info

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
        choices=['grid', 'flat', 'gouraud', 'phong'],
        default='gouraud',
        help='shading mode')

    argp.add_argument(
        '--fow', type=int,
        default=45,
        help='field of view for projective perspective')

    return argp.parse_args()


def main(argv):
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
    log('initializing glut:%s' % delim)
    scene = render.Scene.Instance()
    scene.setShading(args.shading)
    scene.setBackground((0.3, 0.3, 0.3, 0.))
    scene.callback = glt.glutSwapBuffers
    scene.repaint = glt.glutPostRedisplay

    # create camera
    cam = render.Camera.Instance()
    cam.offset = 2
    cam.fow = args.fow
    cam.ratio = ratio
    cam.mode = cam.ORTHOGONALLY
    scene.camera = cam

    # create entities
    log('parsing and inintializing geometries:%s' % delim)
    for obj in parser.ObjParser(args.filename).objects:
        polyhedron = geometry.Polyhedron(obj)
        scene.addEntity(polyhedron)

    #
    #   BIND HANDLER
    #
    log('listening:%s' % delim)

    def rotate():  # TODO remove
        for ent in scene.entities:
            ent.geometry.angle += 1
        scene.repaint()

    glt.glutMouseFunc(scene.evt.mouseClicked)
    glt.glutMotionFunc(scene.evt.mouseMove)
    glt.glutKeyboardFunc(scene.evt.keyPressed)
    glt.glutDisplayFunc(scene.render)
    # glt.glutIdleFunc(rotate)

    # dispatch
    glt.glutMainLoop()


if __name__ == '__main__':
    main(sys.argv)
