#version 330 core

/*
uniform vec4 color;
*/
in vec3 color;
out vec4 out_color;

void
main()
{
    //out_color = vec4(color, 1.0);
    out_color = vec4(1);
}
