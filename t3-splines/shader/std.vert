/*
 *    Basic vertex shader
 */


uniform mat4 mvpmat;
uniform vec4 ucolor;

attribute vec4 vertex;

varying vec4 color;

void main(void) {
    color = ucolor;
    gl_Position = mvpmat * vertex;
}