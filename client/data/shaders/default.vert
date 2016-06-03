#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

uniform mat4 transform;
uniform mat4 modelview;
uniform mat4 projection;

out vec3 transformed_position;
out vec3 transformed_normal;
out vec3 eye;

void
main()
{
    eye = vec3(-modelview[3]);
    transformed_normal = normalize(mat3(modelview) * mat3(transform) * normal);
    transformed_position = vec3(modelview * transform * vec4(position, 1.0));
    gl_Position = projection * vec4(transformed_position, 1.0);
}
