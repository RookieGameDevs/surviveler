#version 330 core

layout(location = 0) in vec3 pos;
out vec3 color;

void
main()
{
    color = pos;
    gl_Position = vec4(pos, 1.0);
}
