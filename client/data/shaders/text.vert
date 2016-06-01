#version 330 core

layout(location = 0) in vec3 in_pos;
uniform mat4 transform;
uniform mat4 modelview;
uniform mat4 projection;

out vec2 uv;

void
main()
{
    uv = vec2(in_pos);
    gl_Position = projection * modelview * transform * vec4(in_pos, 1.0);
}
