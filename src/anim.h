#pragma once

#include "matlib.h"
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
	Vec rot;    // rotation expressed in euler angles
	Vec trans;  // translation
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
	struct Skeleton *skeleton;    // reference skeleton
	float frames_per_second;      // number of frames played per second
	size_t pose_count;            // total number of poses in the animation
	struct SkeletonPose *poses;   // poses
};
