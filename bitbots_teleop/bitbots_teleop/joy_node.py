#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import threading

import rclpy
from humanoid_league_msgs.action import PlayAnimation
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.action import ActionClient
import copy

from pathlib import Path
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from humanoid_league_msgs.msg import Audio, HeadMode
from bitbots_msgs.msg import JointCommand

#from bitbots_animation_server.action import PlayAnimationAction


class JoyNode(Node):
    """ This node controls the roboter via Gamepad.
    """

    #TODO read max values from config

    def __init__(self):
        super().__init__('joy_node')

        self.declare_parameter('type', "noname")
        self.declare_parameter('head', False)

        for controller_type in ["noname", "xbox"]:
            self.declare_parameter(f'{controller_type}.walking.gain_x', 0.0) 
            self.declare_parameter(f'{controller_type}.walking.stick_x', 0)
            self.declare_parameter(f'{controller_type}.walking.gain_y', 0.0)
            self.declare_parameter(f'{controller_type}.walking.stick_y', 0)
            self.declare_parameter(f'{controller_type}.walking.stick_left', 0)
            self.declare_parameter(f'{controller_type}.walking.stick_right', 0)
            self.declare_parameter(f'{controller_type}.walking.duo_turn', False)
            self.declare_parameter(f'{controller_type}.walking.gain_turn', 0.0)
            self.declare_parameter(f'{controller_type}.head.gain_tilt', 0.0)
            self.declare_parameter(f'{controller_type}.head.stick_tilt', 0)
            self.declare_parameter(f'{controller_type}.head.gain_pan', 0.0)
            self.declare_parameter(f'{controller_type}.head.stick_pan', 0)
            self.declare_parameter(f'{controller_type}.kick.btn_left', 0)
            self.declare_parameter(f'{controller_type}.kick.btn_right', 0)
            self.declare_parameter(f'{controller_type}.misc.btn_cheering', 0)

        selected_controller_type = self.get_parameter("type").get_parameter_value().string_value

        self.config = {}
        self.config["walking"] = {
            "gain_x": self.get_parameter(f"{selected_controller_type}.walking.gain_x").get_parameter_value().double_value,
            "stick_x": self.get_parameter(f"{selected_controller_type}.walking.stick_x").get_parameter_value().integer_value,
            "gain_y": self.get_parameter(f"{selected_controller_type}.walking.gain_y").get_parameter_value().double_value,
            "stick_y": self.get_parameter(f"{selected_controller_type}.walking.stick_y").get_parameter_value().integer_value,
            "stick_right": self.get_parameter(f"{selected_controller_type}.walking.stick_right").get_parameter_value().integer_value,
            "stick_left": self.get_parameter(f"{selected_controller_type}.walking.stick_left").get_parameter_value().integer_value,
            "duo_turn": self.get_parameter(f"{selected_controller_type}.walking.duo_turn").get_parameter_value().bool_value,
            "gain_turn": self.get_parameter(f"{selected_controller_type}.walking.gain_turn").get_parameter_value().double_value,
        }

        self.config["head"] = {
            "gain_tilt": self.get_parameter(f"{selected_controller_type}.head.gain_tilt").get_parameter_value().double_value,
            "stick_tilt": self.get_parameter(f"{selected_controller_type}.head.stick_tilt").get_parameter_value().integer_value,
            "gain_pan": self.get_parameter(f"{selected_controller_type}.head.gain_pan").get_parameter_value().double_value,
            "stick_pan": self.get_parameter(f"{selected_controller_type}.head.stick_pan").get_parameter_value().integer_value,
        }
        self.config["kick"] = {
            "btn_left": self.get_parameter(f"{selected_controller_type}.kick.btn_left").get_parameter_value().integer_value,
            "btn_right": self.get_parameter(f"{selected_controller_type}.kick.btn_right").get_parameter_value().integer_value,
        }

        self.config["misc"] = {
            "btn_cheering": self.get_parameter(f"{selected_controller_type}.misc.btn_cheering").get_parameter_value().integer_value,
        }

        print(self.config)

        # --- Initialize Topics ---
        self.create_subscription(Joy,"joy", self.joy_cb, 1)
        self.speak_pub = self.create_publisher(Audio, 'speak', 1)
        self.speak_msg = Audio()

        self.speak_msg.priority = 1

        self.walk_publisher = self.create_publisher(Twist, 'cmd_vel', 1)

        self.walk_msg = Twist()
        self.last_walk_msg = Twist()

        self.walk_msg.linear.x = 0.0
        self.walk_msg.linear.y = 0.0
        self.walk_msg.linear.z = 0.0

        self.walk_msg.angular.x = 0.0
        self.walk_msg.angular.y = 0.0
        self.walk_msg.angular.z = 0.0

        self.head_pub = self.create_publisher(JointCommand, "head_motor_goals", 1)

        self.head_mode_pub = self.create_publisher(HeadMode, "head_mode", 1)

        self.head_msg = JointCommand()
        self.head_msg.max_currents = [-1.0] * 2
        self.head_msg.velocities = [5.0] * 2
        self.head_msg.accelerations = [40.0] * 2

        self.head_modes = HeadMode()

        # --- init animation action ---
        #self.anim_client = ActionClient(self, PlayAnimationAction, 'animation')
        #self.anim_goal = PlayAnimationAction.Goal()
        #self.anim_goal.hcm = False

        #first_try = self.anim_client.wait_for_server(Duration(seconds=1))

        #if not first_try:
        #    self.get_logger().error(
        #        "Animation Action Server not running! Teleop can not work without animation action server. "
        #        "Will now wait until server is accessible!")
        #self.anim_client.wait_for_server()
        #self.get_logger().warn("Animation server running, will go on.")


    def play_animation(self, name):
        return
        self.anim_goal.animation = name
        self.anim_client.send_goal_async(self.anim_goal)
        self.anim_client.wait_for_result()

    def send_text(self, text):
        self.speak_msg.text = text
        self.speak_pub.publish(self.speak_msg)
        # don't send it multiple times
        self.get_clock().sleep_for(Duration(seconds=0.1))

    def set_head_mode(self, mode):
        msg = HeadMode()
        msg.head_mode = mode
        self.head_mode_pub.publish(msg)

    def denormalize_joy(self, gain, axis, msg, deadzone=0.0):
        if abs(msg.axes[axis]) > deadzone:
            return gain * msg.axes[axis]
        else:
            return 0

    def joy_cb(self, msg):
        # forward and sideward walking with left joystick
        self.walk_msg.linear.x = float(self.denormalize_joy(
            self.config['walking']['gain_x'],
            self.config['walking']['stick_x'],
            msg, 0.01))
        self.walk_msg.linear.y = float(self.denormalize_joy(
            self.config['walking']['gain_y'],
            self.config['walking']['stick_y'],
            msg, 0.01))

        # angular walking with shoulder buttons
        turn = msg.axes[self.config['walking']['stick_left']]
        if self.config['walking']['duo_turn']:
            turn -= msg.axes[self.config['walking']['stick_right']]
        turn *= self.config['walking']['gain_turn']

        if turn != 0:
            self.walk_msg.angular.z = float(turn)
        else:
            self.walk_msg.angular.z = 0.0

        # only publish changes
        if self.walk_msg != self.last_walk_msg:
            self.walk_publisher.publish(self.walk_msg)
        self.last_walk_msg = copy.deepcopy(self.walk_msg)

        # head movement with right joystick
        if self.get_parameter("head").get_parameter_value().bool_value:
            pan_goal = float(self.denormalize_joy(
                self.config['head']['gain_pan'],
                self.config['head']['stick_pan'],
                msg, -1))
            tilt_goal = float(self.denormalize_joy(
                self.config['head']['gain_tilt'],
                self.config['head']['stick_tilt'],
                msg, -1))

            self.head_msg.joint_names = ["HeadPan", "HeadTilt"]
            self.head_msg.positions = [pan_goal, tilt_goal]
            self.head_pub.publish(self.head_msg)

        # kicking with upper shoulder buttons
        if msg.buttons[4]:
            # L1
            self.play_animation("kick_left")
        elif msg.buttons[5]:
            # R1
            self.play_animation("kick_right")
        # animations with right buttons
        elif msg.buttons[0]:
            # 1
            self.play_animation("cheering")
        elif msg.buttons[1]:
            # 2
            self.set_head_mode(self.head_modes.BALL_MODE)
        elif msg.buttons[2]:
            # 3
            self.set_head_mode(self.head_modes.FIELD_FEATURES)
        elif msg.buttons[3]:
            # 4
            self.send_text("Button not in use")

        # espeak with left buttons
        if msg.axes[5] > 0:
            # up arrow
            self.send_text("Bit Bots four!")
        elif msg.axes[5] < 0:
            # down arrow
            self.send_text("Yaaaaaaaay!")
        elif msg.axes[4] > 0:
            # left arrow
            self.send_text("Goal!")
        elif msg.axes[4] < 0:
            # right arrow
            self.send_text("Thank you university hamburg for funding.")

def main():
    rclpy.init(args=None)
    node = JoyNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()

