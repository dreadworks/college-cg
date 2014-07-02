
layout(lines) in;
layout(line_strip, max_vertices=4) out;

uniform int spline;
uniform int interpolations;

void main(void)
{
    // pass non spline vertex data through
    if (!spline)
    {
        int i;

        for (i=0; i<gl_in.length(); i++)
        {
            gl_Position = gl_in[i].gl_Position;
            EmitVertex();
        }

        EndPrimitive();
    }

}
