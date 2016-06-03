#version 330 core

in vec3 transformed_normal;
in vec3 origin;
in vec3 eye;

uniform vec4 color_ambient;
uniform vec4 color_diffuse;
uniform vec4 color_specular;

uniform Light {
    vec4 color;
    vec3 position;
} light[1];

out vec4 out_color;

void
main()
{
    vec3 direction = normalize(light[0].position - origin);
    vec3 halfvector = normalize(direction + normalize(eye - origin));

    float diffuse = max(0.0, dot(transformed_normal, direction));
    float specular;
    float shininess = 60;
    if (diffuse > 0) {
        specular = pow(dot(transformed_normal, halfvector), shininess);
    }
    else {
        specular = 0;
    }
    out_color = (
        color_ambient +
        color_diffuse * light[0].color * diffuse +
        color_specular * light[0].color * specular
    );
    out_color.a = 1.0;
}
