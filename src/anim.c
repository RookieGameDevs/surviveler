#include "anim.h"
#include <assert.h>
#include <stdbool.h>
#include <string.h>

#define ROOT_NODE_ID 255

/**
 * Find the skeleton key poses indices for given timestamp.
 */
static void
find_poses(struct Animation *anim, float time, size_t *r_key0, size_t *r_key1)
{
	size_t i = 0;
	for (; i < anim->pose_count - 1; i++) {
		if (time < anim->timestamps[i + 1])
			break;
	}
	*r_key0 = i;
	*r_key1 = i + 1;
}

static void
joint_compute_rotation(struct JointPose *p0, struct JointPose *p1, float time, Mat *r_rm)
{
	Qtr rot;
	qtr_lerp(&p0->rot, &p1->rot, time, &rot);
	*r_rm = mat_from_qtr(&rot);
}

static void
joint_compute_scale(struct JointPose *p0, struct JointPose *p1, float time, Mat *r_sm)
{
	Vec scale;
	vec_lerp(&p0->scale, &p1->scale, time, &scale);
	mat_ident(r_sm);
	mat_scalev(r_sm, &scale);
}

static void
joint_compute_translation(struct JointPose *p0, struct JointPose *p1, float time, Mat *r_tm)
{
	Vec trans;
	vec_lerp(&p0->trans, &p1->trans, time, &trans);
	mat_ident(r_tm);
	mat_translatev(r_tm, &trans);
}

/**
 * Compute joint pose transformation.
 *
 * This function computes the joint pose transformation for given timestamp by
 * interpolating between the provided key poses.
 * In order to compute the transformation, the function computes the entire
 * parent chain of transformations up to the root node. The pose transformation
 * for each traversed node will be stored in the provided array and the process
 * keeps track of already computed chains and re-uses them.
 */
static Mat*
joint_compute_pose(
	struct Animation *anim,
	struct SkeletonPose *sp0,
	struct SkeletonPose *sp1,
	uint8_t joint_id,
	float time,
	Mat *transforms,
	bool *computed
) {
	Mat *t = &transforms[joint_id];

	if (!computed[joint_id]) {
		struct Joint *joint = &anim->skeleton->joints[joint_id];

		// lookup the previous and current joint poses
		struct JointPose *p0 = &sp0->joint_poses[joint_id];
		struct JointPose *p1 = &sp1->joint_poses[joint_id];

		// compute interpolated local joint transform
		Mat tm, rm, sm, tmp;
		mat_ident(t);
		joint_compute_translation(p0, p1, time, &tm);
		joint_compute_rotation(p0, p1, time, &rm);
		joint_compute_scale(p0, p1, time, &sm);
		mat_mul(&tm, &rm, &tmp);
		mat_mul(&tmp, &sm, t);
		mat_mul(&joint->inv_bind_pose, t, &tmp);
		*t = tmp;

		// if the joint is not the root, pre-multiply the full parents
		// transformation chain
		if (joint->parent != ROOT_NODE_ID) {
			Mat *parent_t = joint_compute_pose(
				anim,
				sp0,
				sp1,
				joint->parent, time, transforms,
				computed
			);
			mat_mul(parent_t, t, &tmp);
			memcpy(t, &tmp, sizeof(Mat));
		}

		computed[joint_id] = true;
	}

	return t;
}

void
anim_compute_pose(struct Animation *anim, float absolute_time, Mat *transforms)
{
	int n_joints = anim->skeleton->joint_count;

	// joint processing status flags
	bool computed[n_joints];
	memset(computed, 0, sizeof(bool) * n_joints);

	// compute the relative animation time in ticks, which default to 25
	// frames (ticks) per second
	float speed = anim->speed != 0 ? anim->speed : 25.0f;
	float time_in_ticks = absolute_time * speed;
	float local_time = fmod(time_in_ticks, anim->duration);

	// lookup the key poses indices for given timestamp
	size_t key0, key1;
	find_poses(anim, local_time, &key0, &key1);

	// compute the pose time where t = 0 matches pose 0 and t = 1 pose 1
	float t0 = anim->timestamps[key0], t1 = anim->timestamps[key1];
	float pose_time = (local_time - t0) / (t1 - t0);

	// lookup the key poses
	struct SkeletonPose *sp0 = &anim->poses[key0], *sp1 = &anim->poses[key1];

	// for each joint, compute its pose transformation matrix;
	// the process is iterative and keeps track of which joints have already
	// their transformations computed, in order to re-use them and skip
	// their processing
	for (int j = 0; j < n_joints; j++) {
		if (!computed[j]) {
			joint_compute_pose(
				anim,       // animation
				sp0,        // pose before t
				sp1,        // pose after t
				j,          // joint index
				pose_time,  // exact pose time
				transforms, // output transforms array
				computed    // joint processing status array
			);
		}
	}
}
