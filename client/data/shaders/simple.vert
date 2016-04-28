#version 330 core

layout(location = 0) in vec3 pos;
uniform mat4 transform;
out vec3 color;

void
main()
{
    color = 0.5 + pos;
    gl_Position = transform * vec4(pos, 1.0);
}
