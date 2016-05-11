#version 330 core

in vec2 uv;
out vec4 out_color;

void
main()
{
    out_color = vec4(uv, 1.0, 1.0);
}
