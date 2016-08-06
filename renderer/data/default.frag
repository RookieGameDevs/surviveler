#version 330 core

in vec3 pos;
in vec3 normal;
in vec2 uv;

uniform sampler2D tex;

uniform vec4 color_ambient;
uniform vec4 color_diffuse;
uniform vec4 color_specular;
uniform float opacity;

/* lighting data */
struct Light {
    vec4 color;
    vec3 position;
    float shininess;
};

uniform int enable_light;
uniform Light lights[1];
uniform vec3 eye;

out vec4 out_color;

void
main()
{
    vec4 color = vec4(0);

    out_color = texture(tex, vec2(uv.x, -uv.y), 0) + color_ambient;

    if (enable_light != 0) {
        vec3 light_dir = normalize(lights[0].position - pos);
        vec3 eye_dir = normalize(eye - pos);
        vec3 half_dir = normalize(light_dir + eye_dir);

        float diffuse = max(dot(normal, light_dir), 0.0);
        float specular = pow(max(dot(normal, half_dir), 0.0), lights[0].shininess);

        out_color += (
            color_diffuse * lights[0].color * diffuse +
            color_specular * lights[0].color * specular
        );
    }
    out_color.a = opacity > 0 ? opacity : 1;
}
