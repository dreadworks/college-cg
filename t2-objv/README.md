OpenGL Object Viewer
====================

Dependencies
------------
- Python 2.7.*
- PyOpenGL

Execution
---------
Just call ./objv.py with the following options:
   
    objv.py [-h] [-v] [-t] [-r RES] [-s {grid,flat,smooth}] [--fow FOW]
               filename

    Render arbitrary .obj files with OpenGL. Currently the .obj directives o, v,
    vn, f and s are supported.

    positional arguments:
      filename              obj file

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         switch to verbose mode
      -t, --trace           very very verbose
      -r RES, --res RES     window size e.g. "500x500"
      -s {grid,flat,smooth}, --shading {grid,flat,smooth}
                            shading mode
      --fow FOW             field of view for projective perspective


For example:

    ./objv.py -v -r 800x600 data/bunny.obj

Options
-------

When the object is rendered, the following interaction is possible:

1. Using the mouse:
   - Clicking and holding the left mouse button rotates the object
   - Clicking and holding the middle mouse button zooms
   - Clicking and holding the right mouse button moves the object

2. Using the keyboard:
   - Change the perspective by pressing o for orthogonally and
     p for projective perspective.
   - Colors can be changed by holding r, g, b, s, w and R, G, B, S, W
     to add or remove color components. When pressing q the mode gets
     changed to whether the object or scene background color gets changed.
   - Pressing h toggles the rendering of an object shadow. The shadow
     is only visible when the perspective is set projective.
   - The shading model may be switched with j, k and l, where j is
     'grid', k is 'flat' and l is 'smooth'
