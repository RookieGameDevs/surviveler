#version 330 core

in vec3 transformed_normal;

uniform vec4 color_ambient;
uniform vec4 color_diffuse;
uniform vec4 color_specular;

uniform Light {
    vec4 color;
    vec3 direction;
    vec3 halfvector;
} light;

out vec4 out_color;

void
main()
{
	float diffuse = max(0.0, dot(transformed_normal, light.direction));
	float specular;
	float shininess = 60;
	if (diffuse > 0) {
		specular = pow(dot(transformed_normal, light.halfvector), shininess);
	}
	else {
		specular = 0;
	}
	out_color = (
		color_ambient +
		color_diffuse * light.color * diffuse +
		color_specular * light.color * specular
	);
	out_color.a = 1.0;
}
