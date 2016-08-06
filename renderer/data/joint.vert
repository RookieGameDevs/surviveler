#version 330

layout(location=0) in vec3 in_position;

uniform mat4 projection;
uniform mat4 modelview;
uniform mat4 transform;

void
main()
{
	gl_Position = (
		projection *
		modelview *
		transform *
		vec4(in_position, 1.0)
	);
}
