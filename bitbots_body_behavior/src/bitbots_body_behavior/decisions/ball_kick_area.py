from dynamic_stack_decider.abstract_decision_element import AbstractDecisionElement


class BallKickArea(AbstractDecisionElement):
    def __init__(self, blackboard, dsd, parameters=None):
        super(BallKickArea, self).__init__(blackboard, dsd, parameters)
        self.max_kick_distance = self.blackboard.config['max_kick_distance']
        self.right_kick_min_x = self.blackboard.config['right_kick_min_x']
        self.right_kick_min_y = self.blackboard.config['right_kick_min_y']
        self.right_kick_max_x = self.blackboard.config['right_kick_max_x']
        self.right_kick_max_y = self.blackboard.config['right_kick_max_y']
        self.left_kick_min_x = self.blackboard.config['left_kick_min_x']
        self.left_kick_min_y = self.blackboard.config['left_kick_min_y']
        self.left_kick_max_x = self.blackboard.config['left_kick_max_x']
        self.left_kick_max_y = self.blackboard.config['left_kick_max_y']

    def perform(self, reevaluate=False):
        ball_position = self.blackboard.world_model.get_ball_position_uv()
        if self.right_kick_min_x <= ball_position[0] <= self.right_kick_max_x and \
           self.right_kick_min_y <= ball_position[1] <= self.right_kick_max_y:
            return 'RIGHT'
        if self.left_kick_min_x <= ball_position[0] <= self.left_kick_max_x and \
           self.left_kick_min_y <= ball_position[1] <= self.left_kick_max_y:
            return 'LEFT'
        # TODO: areas for TURN RIGHT/LEFT/AROUND might be useful.
        return 'FAR'

    def get_reevaluate(self):
        """
        As the position of the ball relative to the robot changes even without actions of the robot,
        this needs to be reevaluated.
        :return: True. Always. Trust me.
        """
        return True
