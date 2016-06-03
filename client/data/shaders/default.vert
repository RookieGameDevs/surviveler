#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

uniform mat4 transform;
uniform mat4 modelview;
uniform mat4 projection;

out vec3 transformed_normal;
out vec3 origin;
out vec3 eye;

void
main()
{
    eye = vec3(-modelview[3]);
    mat4 mt = modelview * transform;
    origin = vec3(mt[3]);
    transformed_normal = normalize(mat3(mt) * normal);
    gl_Position = projection * mt * vec4(position, 1.0);
}
