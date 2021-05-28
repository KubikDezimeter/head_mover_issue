# -*- coding:utf-8 -*-
import rospy

from dynamic_stack_decider.abstract_decision_element import AbstractDecisionElement


class GameStateDecider(AbstractDecisionElement):
    def __init__(self, blackboard, dsd, parameters=None):
        super(GameStateDecider, self).__init__(blackboard, dsd, parameters)
        self.game_states = {
            0: 'INITIAL',
            1: 'READY',
            2: 'SET',
            3: 'PLAYING',
            4: 'FINISHED',
        }

    def perform(self, reevaluate=False):
        """
        Translates GameState in Blackboard into DSD Answer
        :param reevaluate:
        :return:
        """
        if not self.blackboard.gamestate.is_allowed_to_move():
            rospy.loginfo_throttle(3.0, "Not allowed to move")
            return "NOT_ALLOWED_TO_MOVE"

        game_state_number = self.blackboard.gamestate.get_gamestate()
        #todo this is a temporary hack to make GUI work
        if game_state_number == 0:
            return "INITIAL"
        elif game_state_number == 1:
            return "READY"
        elif game_state_number == 2:
            return "SET"
        elif game_state_number == 3:
            return "PLAYING"
        elif game_state_number == 4:
            return "FINISHED"

    def get_reevaluate(self):
        """
        Game state can change during the game
        """
        return True
