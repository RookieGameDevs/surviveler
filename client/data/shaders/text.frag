#version 330 core

in vec2 uv;

uniform sampler2D tex;
uniform vec3 color;
uniform int width;
uniform int height;

out vec4 out_color;

void
main()
{
    float u = uv.x / float(width);
    float v = uv.y / float(height);
    float level = texture(tex, vec2(u, v)).r > 0.0 ? 1.0 : 0.0;
    out_color = vec4(color * level, level);
}
