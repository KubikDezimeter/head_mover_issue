#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math
import collections
import numpy as np
import rospy
from bitbots_localisation.localization_objects import Particle, Field
from humanoid_league_msgs.msg import Position, GoalRelative
from nav_msgs.msg import Odometry


class Locator:

    def __init__(self):
        rospy.logdebug("Init Localisation")
        rospy.init_node('bitbots_localisation', anonymous=False)

        self.pub = rospy.Publisher("/local_position", Position, queue_size=1)

        rospy.Subscriber("/odometry", Odometry, self.update_position)
        rospy.Subscriber("/goal_relative", GoalRelative, self.perform)

        self.conf__nr_particle = 100 # rospy.get_param("/localisation/nr_particle")
        self.debug = rospy.get_param("/debug_active", False)

        # Setup variables
        self._setup()

        # Get data and update model
        rospy.spin()

    def _setup(self):
        self.fieldmodel = Field()
        dim = self.fieldmodel.get_dimensions()
        # self.particles = Particle.create_n_random(nr_particle, 0, *dim[1:])

        # create new matrix with particles
        self.particlem = np.empty((self.conf__nr_particle, 3), np.int8)
        """
        x, y, r
        ...
        """

        # initialize particle matrix
        for n in range(self.conf__nr_particle):
            self.particlem[n, 0] = np.random.randint(0, dim[2])
            self.particlem[n, 1] = np.random.randint(dim[1], dim[3])
            self.particlem[n, 2] = np.random.randint(0, 359)

        # Setzte noch andere Variablen für später
        self.last_movement_approx = (0, 0)
        self.field = Field()

    #def update_position(self, odoemetry: Odometry)->None:
    def update_position(self, odometry):

        self.last_movement_approx = odometry.pose.pose.position.x , odometry.twist.twist.angular[0] #todo correct access

        # update Position for all particle:

        # for particle in self.particles:
        #    particle.rotate(self.last_movement_approx[1])
        #    particle.move_forward(self.last_movement_approx[0])

        self.particlem[:, 2] += self.last_movement_approx[1]
        fx = np.vectorize(lambda xm:  self.last_movement_approx[0] * math.cos(math.radians(xm)))
        fy = np.vectorize(lambda xm:  self.last_movement_approx[0] * math.sin(math.radians(xm)))
        self.particlem[:, 0] += fx(self.particlem[:, 2])
        self.particlem[:, 1] += fy(self.particlem[:, 2])


    #def perform(self, goals: GoalsRealtive)->None:
    def perform(self, goals):
        nr_particle = self.conf__nr_particle
        # Measurment for all Particles
        #r_mes = self.sensor_data()

        # real meassurment
        mesgoal_r = goals

        #mesgoal_p = np.zeros((nr_particle, 8), np.int)
        # Create performant Weightlist
        weights = collections.deque([], nr_particle)

        for i in range(nr_particle):
            #mesgoal_p[i, :] =
            # meassurement for all particles
            mes = self.field.mes_goals(self.particlem[i, :].tolist())
            dist = self.mes_dist(mesgoal_r, mes)
            weights.append(1.0 / dist if (abs(dist) - 0.5) > 0 else 0)


        #for particle in self.particles:
            #p_mes = self.particle_mes(particle)
            #dist = self.mes_dist(r_mes, p_mes)

            #particle.weight = 1/dist

        # Write out best particle
        # Todo clustering? Besser aber kostet noch mehr Laufzeit
        best_index = weights.index(max(weights))
        x, y, r = self.particlem[best_index, :]

        msg = Position()
        msg.pose.x = x
        msg.pose.y = y
        msg.pose.theta = r
        msg.confidence = weights[best_index]

        # Publish information
        self.pub.publish(msg)


        # Recalculate distribution

        # Normalize Weights
        weightsum = sum(weights)

        nw = collections.deque([], nr_particle)

        #Liegen Daten vor?
        if weightsum != 0:
            for x in range(nr_particle):
                nw.append(weights.popleft()/weightsum)
                #nw.append(weights.pop()/weightsum)
        else:
            for x in range(nr_particle):
                nw.append(1.0/nr_particle)


        #weights /= weightsum
        weights = nw
        # Resample all Particles

        # Neue Partikel einstreuen
        nr_new = int(nr_particle / 10)  # TODO Mache konfigurierbar
        nr_new = 0
        nr_stay = nr_particle - nr_new

        # Wähle Zufällig gute Partikel aus (gewichtet/duplikate möglich)
        selceted = np.random.choice(nr_particle, nr_stay, p=weights)

        # Create new arry for old an new particles
        new_particles = np.empty((nr_particle, 3))

        # Randomize all old particles and add to new collection
        for i in range(nr_stay):
            new_particles[i, 0] = self.particlem[selceted[i], 0] + np.random.normal(0, 15)
            new_particles[i, 1] = self.particlem[selceted[i], 1] + np.random.normal(0, 15)
            new_particles[i, 2] = self.particlem[selceted[i], 2] + np.random.normal(0, 15)

        # Add new particles to collection
        dim = self.fieldmodel.get_dimensions()
        for i in range(nr_stay, nr_particle):
            new_particles[i, :] = np.asarray([np.random.randint(0, dim[2]),
                                              np.random.randint(dim[1], dim[3]),
                                              np.random.randint(0, 360)])

        #new_particles = []

        #for _ in range(nr_particle):
        #    part = copy.deepcopy(distr.pick())
        #
        #            part.x += random.gauss(0, 10)
        #            part.y += random.gauss(0, 10)
        #            part.r += random.gauss(0, 10)
        #
        #            new_particles.append(part)

        #new_particles.extend(Particle.create_n_random(nr_particle - len(new_particles), *self.fieldmodel.get_dimensions()))

        self.particlem = new_particles

    @staticmethod
    # def mes_dist(r_mes: List[float], p_mes: tuple)-> int:
    def mes_dist(r_mes, p_mes):
        """
        Measures the ditance between two mesurements
        :param r_mes:
        :param p_mes:
        :return:
        """

        goaldistances = []
        for ireal in range(len(r_mes)):
            distances = [math.sqrt((r_mes[ireal][0]-par[0])**2 + (r_mes[ireal][1]-par[1])**2)for par in p_mes]
            goaldistances.append(min(distances))

        return sum(goaldistances)  # todo weitere features


if __name__ == "__main__":
    Locator()
