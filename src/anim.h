#pragma once

#include "matlib.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/**
 * Joint of a skeleton.
 */
struct Joint {
	Mat inv_bind_pose;  // inverse bind pose transform
	uint8_t parent;     // index of the parent joint or 0xff if root
};

/**
 * Skeleton as collection of joints.
 */
struct Skeleton {
	uint8_t joint_count;   // total number of joints in the skeleton
	struct Joint *joints;  // joints
};


/**
 * Joint pose (e.g transformation).
 */
struct JointPose {
	Vec trans;  // translation
	Qtr rot;    // rotation quaternion
	Vec scale;  // scale
};

/**
 * Skeleton pose as a collection of per-joint poses.
 */
struct SkeletonPose {
	struct Skeleton *skeleton;      // reference skeleton
	struct JointPose *joint_poses;  // joint poses array; must match number of joints in the skeleton
};

/**
 * Animation as a collection of clips.
 */
struct Animation {
	char *name;                   // animation name
	struct Skeleton *skeleton;    // reference skeleton
	float duration;               // duration in ticks
	float speed;                  // number of ticks played per second
	size_t pose_count;            // total number of poses in the animation
	float *timestamps;            // animation timeline
	struct SkeletonPose *poses;   // poses
};

/**
 * Animation playback instance.
 */
struct AnimationInstance {
	struct Animation *anim;  // reference animation
	float time;              // local clock
	Mat *joint_transforms;   // local joint transformations
	Mat *skin_transforms;    // final skinning transformations
	bool *processed_joints;  // joint processing flags (private)
};

/**
 * Create an instance of given animation.
 */
struct AnimationInstance*
anim_new_instance(struct Animation *anim);

/**
 * Destroy animation instance.
 */
void
anim_free_instance(struct AnimationInstance *inst);

/**
 * Advance the animation by given time delta
 */
void
anim_play(struct AnimationInstance *anim_inst, float dt);
