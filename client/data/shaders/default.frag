#version 330 core

in vec3 transformed_normal;

uniform vec4 color_ambient;
uniform vec4 color_diffuse;
uniform vec4 color_specular;

uniform vec4 light_color;
uniform vec3 light_direction;
uniform vec3 light_halfvector;

out vec4 out_color;

void
main()
{
	float diffuse = max(0.0, dot(transformed_normal, light_direction));
	float specular;
	float shininess = 60;
	if (diffuse > 0) {
		specular = pow(dot(transformed_normal, light_halfvector), shininess);
	}
	else {
		specular = 0;
	}
	out_color = (
		color_ambient +
		color_diffuse * light_color * diffuse +
		color_specular * light_color * specular
	);
	out_color.a = 1.0;
}
