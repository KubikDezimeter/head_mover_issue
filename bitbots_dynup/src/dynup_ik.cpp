#include <bitbots_dynup/dynup_ik.h>
namespace bitbots_dynup {
void DynupIK::init(moveit::core::RobotModelPtr kinematic_model) {
  /* Extract joint groups from kinematics model */
  l_leg_joints_group_ = kinematic_model->getJointModelGroup("LeftLeg");
  r_leg_joints_group_ = kinematic_model->getJointModelGroup("RightLeg");
  l_arm_joints_group_ = kinematic_model->getJointModelGroup("LeftArm");
  r_arm_joints_group_ = kinematic_model->getJointModelGroup("RightArm");
  all_joints_group_ = kinematic_model->getJointModelGroup("All");

  /* Reset kinematic goal to default */
  goal_state_.reset(new robot_state::RobotState(kinematic_model));
  goal_state_->setToDefaultValues();

  const Eigen::Isometry3d &end_effector_state = goal_state_->getGlobalLinkTransform("r_sole");
}

void DynupIK::reset() {
  /* We have to set some good initial position in the goal state,
   * since we are using a gradient based method. Otherwise, the
   * first step will be not correct */
  //TODO: add hands or replace with actual values?
  std::vector<std::string> names_vec = {"LHipPitch", "LKnee", "LAnklePitch", "RHipPitch", "RKnee", "RAnklePitch"};
  std::vector<double> pos_vec = {0.7, -1.0, -0.4, -0.7, 1.0, 0.4};
  for (int i = 0; i < names_vec.size(); ++i) {
    goal_state_->setJointPositions(names_vec[i], &pos_vec[i]);
  }
}

bitbots_splines::JointGoals DynupIK::calculate(const DynupResponse &ik_goals) {

  tf2::Transform right_foot_goal = ik_goals.r_foot_goal_pose;
  tf2::Transform left_foot_goal = ik_goals.l_foot_goal_pose * ik_goals.r_foot_goal_pose;
  tf2::Transform left_hand_goal = ik_goals.l_hand_goal_pose;
  tf2::Transform right_hand_goal = ik_goals.r_hand_goal_pose;

  geometry_msgs::Pose right_foot_goal_msg, left_foot_goal_msg, right_hand_goal_msg, left_hand_goal_msg;

  tf2::toMsg(right_foot_goal, right_foot_goal_msg);
  tf2::toMsg(left_foot_goal, left_foot_goal_msg);
  tf2::toMsg(right_hand_goal, right_hand_goal_msg);
  tf2::toMsg(left_hand_goal, left_hand_goal_msg);


  bool success;

  goal_state_->updateLinkTransforms();

  success = goal_state_->setFromIK(l_leg_joints_group_,
                                   left_foot_goal_msg,
                                   0.01,
                                   moveit::core::GroupStateValidityCallbackFn());
  goal_state_->updateLinkTransforms();
  //ROS_ERROR("1 %d", success);

  success &= goal_state_->setFromIK(r_leg_joints_group_,
                                   right_foot_goal_msg,
                                   0.01,
                                   moveit::core::GroupStateValidityCallbackFn());
  goal_state_->updateLinkTransforms();
  //ROS_ERROR("2 %d", success);
  
  //ROS_ERROR("3p %f, %f, %f", left_hand_goal_msg.position.x, left_hand_goal_msg.position.y, left_hand_goal_msg.position.z);
  //double r, p, y;
  //tf2::Matrix3x3(left_hand_goal.getRotation()).getRPY(r, p, y);
  //ROS_ERROR("3o %f, %f, %f", r, p, y); 
  success &= goal_state_->setFromIK(l_arm_joints_group_,
                                   left_hand_goal_msg,
                                   0.01,
                                   moveit::core::GroupStateValidityCallbackFn());
  goal_state_->updateLinkTransforms();
  //ROS_ERROR("3 %d", success);

  //ROS_ERROR("4p %f, %f, %f", right_hand_goal_msg.position.x, right_hand_goal_msg.position.y, right_hand_goal_msg.position.z);
  //tf2::Matrix3x3(left_hand_goal.getRotation()).getRPY(r, p, y);
  //ROS_ERROR("4o %f, %f, %f", r, p, y); 
  success &= goal_state_->setFromIK(r_arm_joints_group_,
                                   right_hand_goal_msg,
                                   0.01,
                                   moveit::core::GroupStateValidityCallbackFn());
  //ROS_ERROR("4 %d", success);
  

  if (success) {
    /* retrieve joint names and associated positions from  */
    std::vector<std::string> joint_names = all_joints_group_->getActiveJointModelNames();
    std::vector<double> joint_goals;
    goal_state_->copyJointGroupPositions(all_joints_group_, joint_goals);

    /* construct result object */
    bitbots_splines::JointGoals result;
    result.first = joint_names;
    result.second = joint_goals;
    return result;
  } else {
    return {};
  }
}
void DynupIK::useStabilizing(bool use) {
  use_stabilizing_ = use;
}

void DynupIK::useMinimalDisplacement(bool use) {
  use_minimal_displacement_ = use;
}
}
