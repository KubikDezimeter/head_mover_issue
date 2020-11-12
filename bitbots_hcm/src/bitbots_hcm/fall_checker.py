# -*- coding: utf8 -*-
import array
import math
import numpy
from sensor_msgs.msg import Imu
import rospy

# todo hip pitch offset
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score


class FallChecker(BaseEstimator):

    def __init__(self, thresh_gyro_pitch=rospy.get_param("hcm/falling_thresh_gyro_pitch"),
                 thresh_gyro_roll=rospy.get_param("hcm/falling_thresh_gyro_roll"),
                 thresh_orient_pitch=math.radians(rospy.get_param("hcm/falling_thresh_orient_pitch")),
                 thresh_orient_roll=math.radians(rospy.get_param("hcm/falling_thresh_orient_roll"))):

        self.thresh_gyro_pitch = thresh_gyro_pitch
        self.thresh_gyro_roll = thresh_gyro_roll
        self.thresh_orient_pitch = thresh_orient_pitch
        self.thresh_orient_roll = thresh_orient_roll

        self.STABLE = 0
        self.FRONT = 1
        self.BACK = 2
        self.LEFT = 3
        self.RIGHT = 4

    def check_falling(self, not_much_smoothed_gyro, euler):
        """Checks if the robot is currently falling and in which direction. """
        # Checks if robot is still
        bools = [abs(n) < 0.1 for n in not_much_smoothed_gyro]
        if all(bools):
            return self.STABLE

        # setting the fall quantification function
        roll_fall_quantification = self.calc_fall_quantification(
            self.thresh_orient_roll,
            self.thresh_gyro_roll,
            euler[0],
            not_much_smoothed_gyro[0])

        pitch_fall_quantification = self.calc_fall_quantification(
            self.thresh_orient_pitch,
            self.thresh_gyro_pitch,
            euler[1],
            not_much_smoothed_gyro[1])

        if roll_fall_quantification + pitch_fall_quantification == 0:
            return self.STABLE

        # compare quantification functions
        if pitch_fall_quantification > roll_fall_quantification:
            # detect the falling direction
            if not_much_smoothed_gyro[1] < 0:
                return self.BACK
            # detect the falling direction
            else:
                return self.FRONT
        else:
            # detect the falling direction
            if not_much_smoothed_gyro[0] < 0:
                return self.LEFT
            # detect the falling direction
            else:
                return self.RIGHT

    def calc_fall_quantification(self, falling_threshold_orientation, falling_threshold_gyro, current_axis_euler,
                                 current_axis__gyro):
        # check if you are moving forward or away from the perpendicular position, by comparing the signs.
        if numpy.sign(current_axis_euler) == numpy.sign(current_axis__gyro):
            # calculatiung the orentation skalar for the threshold
            skalar = max((falling_threshold_orientation - abs(current_axis_euler)) / falling_threshold_orientation, 0)
            # checking if the rotation velocity is lower than the the threshold
            if falling_threshold_gyro * skalar < abs(current_axis__gyro):
                # returning the fall quantification function
                return abs(current_axis__gyro) * (1 - skalar)
        return 0

    def fit(self, x, y):
        # we have to do nothing, as we are not actually fitting any model
        rospy.logwarn("You can not train this type of classifier")
        pass

    def score(self, X, y, sample_weight=None):
        return accuracy_score(y, self.predict(X), sample_weight=sample_weight)

    def predict(self, x):
        # only take gyro and orientation from data
        y = []
        for entry in x:
            prediction = self.check_falling(entry[3:6], entry[6:9])
            y.append(prediction)
        return y
