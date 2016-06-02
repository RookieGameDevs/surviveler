#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

uniform mat4 transform;
uniform mat4 modelview;
uniform mat4 projection;

out vec3 transformed_normal;

void
main()
{
	transformed_normal = normalize(mat3(modelview) * mat3(transform) * normal);
	gl_Position = projection * modelview * transform * vec4(position, 1.0);
}
