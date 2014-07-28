/*
 *    Basic vertex shader
 */


uniform mat4 mvpmat;
attribute vec4 vertex;

void main(void)
{
    gl_Position = mvpmat * vertex;
}