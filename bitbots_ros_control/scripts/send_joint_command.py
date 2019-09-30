#!/usr/bin/env python3

import argparse

import rospy

from bitbots_msgs.msg import JointCommand


class PredefinedCommands:
    __ids__ = [
        "HeadPan",
        "HeadTilt",
        "LShoulderPitch",
        "LShoulderRoll",
        "LElbow",
        "RShoulderPitch",
        "RShoulderRoll",
        "RElbow",
        "LHipYaw",
        "LHipRoll",
        "LHipPitch",
        "LKnee",
        "LAnklePitch",
        "LAnkleRoll",
        "RHipYaw",
        "RHipRoll",
        "RHipPitch",
        "RKnee",
        "RAnklePitch",
        "RAnkleRoll"
    ]
    __velocity__ = 5.0
    __accelerations__ = -1.0
    __max_currents__ = -1.0

    Zero = JointCommand(
        joint_names=__ids__,
        velocities=[__velocity__] * len(__ids__),
        accelerations=[__accelerations__] * len(__ids__),
        max_currents=[__max_currents__] * len(__ids__),
        positions=[0.0] * len(__ids__))


def parse_args():
    parser = argparse.ArgumentParser(description="Send a bitbots_msgs/JointCommand to our ros-control node in a loop")
    parser.add_argument("--once", action="store_true", default=False,
                        help="Only send the message once instead of in a loop")
    parser.add_argument("-c", "--command", type=str, help="Command to send. Use one of the available choices",
                        choices=[c for c in PredefinedCommands.__dict__ if not c.startswith("__")],
                        default="Zero")

    return parser.parse_args()


def main():
    args = parse_args()
    joint_command = PredefinedCommands.__dict__[args.command]

    rospy.init_node("send_joint_command")
    pub = rospy.Publisher("/DynamixelController/command", JointCommand, queue_size=1)
    print(joint_command)

    while pub.get_num_connections() < 1:
        rospy.loginfo_once("Waiting until subscribers connect to /DynamixelController/command")
        rospy.sleep(0.1)
    # just to make sure
    rospy.sleep(1)

    rospy.loginfo("Sending controller commands of type {} now".format(args.command))

    while not rospy.is_shutdown():
        joint_command.header.stamp = rospy.Time.now()
        pub.publish(joint_command)
        rospy.sleep(0.5)

        if args.once:
            break


if __name__ == "__main__":
    main()
