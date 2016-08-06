#version 330 core

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;
layout(location = 3) in ivec4 in_joints;
layout(location = 4) in vec4  in_weights;

uniform mat4 transform;
uniform mat4 modelview;
uniform mat4 projection;

uniform int animate;
uniform mat4 joints[100];

out vec3 pos;
out vec3 normal;
out vec2 uv;

void
main()
{
    mat4 joint_transform = mat4(1);
    if (animate != 0) {
        mat4 t = mat4(0);
        bool transformed = false;
        for (int i = 0; i < 4; i++) {
            int joint_id = in_joints[i];
            if (joint_id == 255)
                break;
            t += joints[joint_id] * in_weights[i];
            transformed = true;
        }
        if (transformed)
            joint_transform *= t;
    }

    mat4 view = modelview * transform * joint_transform;
    pos = vec3(view * vec4(in_position, 1.0));
    normal = normalize(mat3(view) * in_normal);
    uv = in_uv;

    gl_Position = projection * vec4(pos, 1.0);
}
