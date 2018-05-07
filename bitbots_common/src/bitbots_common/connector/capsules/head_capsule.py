import math
import numpy as np
import rosparam
import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class HeadCapsule:
    def __init__(self):

        self.config = rosparam.get_param("Behaviour/Head")
        self.delta = self.config["Search"]["headTurnPrecision"]
        self.wait_time = self.config["Search"]["headTurnTime"]
        self.pan_speed_max = self.config["Search"]["maxPanSpeedSearch"]
        self.tilt_speed_max = self.config["Search"]["maxTiltSpeedSearch"]
        self.max_pan = self.config["Camera"]["maxPan"]
        self.min_pan = self.config["Camera"]["minPan"]
        self.max_tilt = self.config["Camera"]["maxTilt"]
        self.min_tilt = self.config["Camera"]["minTilt"]
        self.initial_tilt = self.config["Camera"]["initialTilt"]
        self.camera_height = self.config["Camera"]["cameraHeight"]
        self.ball_height = self.config["Camera"]["ballHeight"]

        # class variables
        self._headmode = 0
        self.confirmed_ball_time = -999
        self.confirmed_goal_time = -999
        self.current_pan_pos = 0
        self.current_tilt_pos = 0
        self.is_ball_tracking_still_active = False

        # preparing message for more performance
        self.pos_msg = JointTrajectory()
        self.pos_msg.joint_names = ["HeadPan", "HeadTilt"]
        self.point_msg = JointTrajectoryPoint()
        self.point_msg.positions = [0, 0]
        self.point_msg.velocities = [0, 0]
        self.pos_msg.points = [self.point_msg]

        self.position_publisher = None  # type: rospy.Publisher

    #################
    # Head position #
    #################

    def send_motor_goals(self, pan_position, pan_speed, tilt_position, tilt_speed):
        self.current_pan_pos = pan_position
        self.current_tilt_pos = tilt_position
        posnew = (math.radians(np.clip(pan_position, self.min_pan, self.max_pan)),
                  math.radians(np.clip(tilt_position, self.min_tilt, self.max_tilt)))
        velnew = (np.clip(pan_speed, 0, self.pan_speed_max),
                  np.clip(tilt_speed, 0, self.tilt_speed_max))
        self.pos_msg.points[0].positions = posnew
        self.pos_msg.points[0].velocities = velnew
        self.pos_msg.header.stamp = rospy.Time.now()
        self.position_publisher.publish(self.pos_msg)

    def get_current_head_pos(self):
        return self.current_pan_pos, self.current_tilt_pos

    def get_headmode(self):
        return self._headmode

    def cb_headmode(self, headmode):
        self._headmode = headmode.headMode

    def joint_state_cb(self, msg):
        i = 0
        for joint in msg.name:
            if joint == "HeadPan":
                self.current_pan_pos = math.degrees(msg.position[i])
            elif joint == "HeadTilt":
                self.current_tilt_pos = math.degrees(msg.position[i])
            i += 1

    def get_pantilt_from_uv(self, u, v):
        # type: (float, float) -> tuple
        cam_height = self.camera_height
        ball_height = self.ball_height
        if (u == 0.0 and v == 0.0) or u is None:
            pan = self.current_pan_pos
            tilt = self.current_tilt_pos
            return pan, tilt
        elif u == 0:
            pan = math.copysign(90, v)
        else:
            pan = math.degrees(math.atan(v/u))

        tilt = self.initial_tilt - math.degrees(math.atan((cam_height - ball_height / 2)/(math.sqrt(u ** 2 + v ** 2))))
        return pan, tilt

    ################
    # Confirm ball #
    ################

    def get_confirmed_ball_time(self):
        return self.confirmed_ball_time

    def set_confirmed_ball_time(self, t=None):
        if not t:
            t = rospy.get_time()
        self.confirmed_ball_time = t

    def unset_confirmed_ball_time(self):
        self.confirmed_ball_time = -999

    ################
    # Confirm goal #
    ################

    def get_confirmed_goal_time(self):
        return self.confirmed_goal_time

    def set_confirmed_goal_time(self, t=None):
        if not t:
            t = rospy.get_time()
        self.confirmed_goal_time = t

    def unset_confirmed_goal_time(self):
        self.confirmed_goal_time = -999
