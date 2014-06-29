/*
 *    Basic vertex shader
 */


uniform mat4 mvpmat;

void main(void) {
    gl_Position = mvpmat * gl_Vertex;
}