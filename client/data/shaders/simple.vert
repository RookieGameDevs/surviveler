#version 330 core

layout(location = 0) in vec3 pos;
uniform mat4 transform;
uniform mat4 projection;
out vec3 color;

void
main()
{
    color = vec3(0.04, 0.67, 0.87);
    gl_Position = projection * transform * vec4(pos, 1.0);
}
