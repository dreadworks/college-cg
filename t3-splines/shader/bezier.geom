#version 120
#extension GL_EXT_geometry_shader4: enable


uniform int interpolations;


vec2 interpolate(in float t, in vec2 u, in vec2 v)
{
    vec2 interpolated;

    interpolated.x = u.x + t * (v.x - u.x);
    interpolated.y = u.y + t * (v.y - u.y);

    return interpolated;
}


vec2 casteljau(in float t)
{
    int size_cpoly, i, j;
    vec2 cpoly[4];

    size_cpoly = 4;
    for (i=0; i<cpoly.length(); i++)
    {
        cpoly[i].xy = gl_PositionIn[i].xy;
    }

    while (size_cpoly > 1)
    {
        for (j=0; j<size_cpoly-1; j++) {
            cpoly[j] = interpolate(t, cpoly[j], cpoly[j+1]);
        }

        size_cpoly -= 1;
    }

    return cpoly[0];
}


void main(void)
{

    int i;
    float size_steps;


    size_steps = float(1) / float(interpolations);
    if (mod(gl_PrimitiveIDIn, 3) == 0)
    {
        for (i=0; i<interpolations; i++)
        {
            gl_Position = vec4(casteljau(size_steps * i), 0, 0);
            EmitVertex();
        }
    }

    EndPrimitive();

}